module.exports = async function(req, res){
  try{
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    if (req.method === 'OPTIONS') return res.status(204).end();
    return res.status(200).json({ ok: true, ts: Date.now(), hasKey: !!process.env.OPENAI_API_KEY });
  }catch(e){
    return res.status(500).json({ ok:false, error: String(e) });
  }
}
