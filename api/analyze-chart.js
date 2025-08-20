module.exports = async function(req, res){
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') return res.status(204).end();
  if(req.method!=='POST') return res.status(405).json({ error: 'Method not allowed' });
  try{
    let body = req.body;
    if(!body){
      body = await new Promise((resolve, reject)=>{
        let data=''; req.on('data', c=>data+=c); req.on('end', ()=>{ try{ resolve(JSON.parse(data||'{}')); }catch(e){ reject(e); } });
      });
    }
    let { candles, want } = body || {};
    if(!Array.isArray(candles) || candles.length<5){
      return res.status(400).json({ error:'Invalid candles' });
    }
    candles = candles.slice(-2000);
    const closes = candles.map(c=>c[4]);
    // ZigZag
    const thr = 0.04; const waves=[]; let dir=0, last=closes[0], idx=0;
    for(let i=1;i<closes.length;i++){
      const p=closes[i]; const chg=(p-last)/last;
      if(dir>=0 && chg<=-thr){ waves.push({i:idx, price:last}); dir=-1; last=p; idx=i; }
      else if(dir<=0 && chg>=thr){ waves.push({i:idx, price:last}); dir=1; last=p; idx=i; }
      if(Math.abs(chg)>thr){ last=p; idx=i; }
    }
    waves.push({i:closes.length-1, price:closes[closes.length-1]});
    // Fib
    let hi=-Infinity, lo=Infinity;
    for(const c of candles){ hi=Math.max(hi, c[2]); lo=Math.min(lo, c[3]); }
    const resp = { ok:true, waves: waves.slice(0,12), fib: (isFinite(hi)&&isFinite(lo)) ? {hi, lo} : null };
    return res.status(200).json(resp);
  }catch(e){ return res.status(500).json({ error:String(e) }); }
}
