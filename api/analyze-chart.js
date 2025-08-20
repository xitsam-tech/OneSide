function zigZag(closes, threshold=0.04){
  const pts=[]; let dir=0; let last=closes[0]; let lastIdx=0;
  for(let i=1;i<closes.length;i++){
    const p=closes[i]; const chg=(p-last)/last;
    if(dir>=0 && chg<=-threshold){ pts.push({i:lastIdx, price:last}); dir=-1; last=p; lastIdx=i; }
    else if(dir<=0 && chg>=threshold){ pts.push({i:lastIdx, price:last}); dir=1; last=p; lastIdx=i; }
    if(Math.abs(chg)>threshold){ last=p; lastIdx=i; }
  }
  pts.push({i:closes.length-1, price:closes[closes.length-1]});
  return pts.slice(0, 12);
}
function fibLevels(candles){
  let hi=-Infinity, lo=Infinity;
  for(const c of candles){ hi=Math.max(hi, c[2]); lo=Math.min(lo, c[3]); }
  if(!isFinite(hi)||!isFinite(lo)) return null;
  return { hi, lo };
}

export default async function handler(req, res){
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') return res.status(204).end();
  if(req.method!=='POST') return res.status(405).json({ error: 'Method not allowed' });
  try{
    const body = req.body || await new Promise((resolve, reject)=>{
      let data=''; req.on('data', c=>data+=c); req.on('end', ()=>{ try{ resolve(JSON.parse(data||'{}')); }catch(e){ reject(e); } });
    });
    let { candles, want } = body || {};
    if(!Array.isArray(candles) || candles.length<5){
      return res.status(400).json({ error:'Invalid candles' });
    }
    // Cap size for safety
    candles = candles.slice(-2000);
    const closes = candles.map(c=>c[4]);
    const resp = { ok:true };
    if(!want || want.fib) resp.fib = fibLevels(candles);
    if(!want || want.waves) resp.waves = zigZag(closes);
    // Optional OpenAI labeling
    if(process.env.USE_OPENAI_CHART==='1' && process.env.OPENAI_API_KEY){
      try{
        const prompt = `Analysiere Preiswellen (Elliott-ähnlich) auf Basis dieser Schlusskurse.
Gib maximal 7 Punkte (Index bezogen auf das Array) als markante Wellen (Hoch/Tief) zurück.
Nur JSON: {"labels":[{"i": <index>, "label": "W1|W2|...|A|B|C"}]}`;
        const r = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`, 'Content-Type':'application/json' },
          body: JSON.stringify({
            model: process.env.OPENAI_MODEL || 'gpt-4o-mini',
            temperature: 0.2,
            messages: [
              { role:'system', content: 'You return strict JSON only.' },
              { role:'user', content: prompt + "\n" + JSON.stringify({ closes }) }
            ]
          })
        });
        if(r.ok){
          const j = await r.json();
          let txt = j.choices?.[0]?.message?.content?.trim() || '{}';
          try{ const parsed = JSON.parse(txt); resp.labels = parsed.labels || []; }catch(_){}
        }
      }catch(_){ /* non-fatal */ }
    }
    return res.status(200).json(resp);
  }catch(e){
    return res.status(500).json({ error:String(e) });
  }
}
