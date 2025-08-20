const fetch = global.fetch || ((...args)=>import('node-fetch').then(({default: f})=>f(...args)));

module.exports = async function(req, res){
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Method not allowed' });
  try{
    if(!process.env.OPENAI_API_KEY){
      return res.status(501).json({ error: 'OPENAI_API_KEY not configured on server' });
    }
    let body = req.body;
    if(!body){
      body = await new Promise((resolve, reject)=>{
        let data=''; req.on('data', c=>data+=c); req.on('end', ()=>{ try{ resolve(JSON.parse(data||'{}')); }catch(e){ reject(e); } });
      });
    }
    const { text, to='en', model } = body || {};
    if(!text || typeof text !== 'string' || text.trim()===''){
      return res.status(400).json({ error: 'Missing "text"' });
    }
    const input = text.slice(0, 8000);
    const tgt = String(to||'en').slice(0,8);
    const useModel = model || process.env.OPENAI_MODEL || 'gpt-4o-mini';
    const prompt = `Übersetze präzise ins ${tgt}. Zahlen, Währungen, Prozent und Eigennamen erhalten. Nur Übersetzung zurückgeben.`;
    const r = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`, 'Content-Type':'application/json' },
      body: JSON.stringify({
        model: useModel,
        temperature: 0.2,
        messages: [
          { role: 'system', content: prompt },
          { role: 'user', content: input }
        ]
      })
    });
    if(!r.ok){
      const t = await r.text();
      return res.status(502).json({ error: 'OpenAI error', status: r.status, body: t });
    }
    const j = await r.json();
    const out = j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content ? j.choices[0].message.content.trim() : '';
    return res.status(200).json({ text: out });
  }catch(e){
    return res.status(500).json({ error: String(e) });
  }
}
