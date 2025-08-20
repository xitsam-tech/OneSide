const fetch = global.fetch || ((...args)=>import('node-fetch').then(({default: f})=>f(...args)));

const STABLE_IDS = new Set(['tether','usd-coin','dai','binance-usd','true-usd','frax','usdd','paxos-standard','gemini-dollar','lusd']);

module.exports = async function(req, res){
  try{
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET,OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    if(req.method==='OPTIONS') return res.status(204).end();

    const urlObj = new URL(req.url, 'http://x');
    const vs = (urlObj.searchParams.get('vs') || 'EUR').toUpperCase();
    const limit = Math.min(250, Math.max(1, parseInt(urlObj.searchParams.get('limit')||'10', 10)));
    const perPage = Math.min(250, limit+20);

    const url = `https://api.coingecko.com/api/v3/coins/markets?vs_currency=${encodeURIComponent(vs)}&order=market_cap_desc&per_page=${perPage}&page=1&sparkline=true&price_change_percentage=24h,7d`;
    const r = await fetch(url, { timeout: 10000 });
    if(!r.ok){
      return res.status(r.status).json({ error: 'CG error', status: r.status });
    }
    const data = await r.json();
    const arr = Array.isArray(data) ? data : [];

    const filtered = arr.filter(c=> !STABLE_IDS.has(String(c.id||'').toLowerCase()) ).slice(0, limit);
    const sumMc = filtered.reduce((a,c)=> a + (+c.market_cap||0), 0) || 1;

    const list = filtered.map(c=>({
      id: String(c.id||'').toLowerCase(),
      name: c.name,
      symbol: String(c.symbol||'').toUpperCase(),
      image: c.image || '',
      price: +c.current_price || 0,
      ch24: +(c.price_change_percentage_24h || 0),
      ch7: +(c.price_change_percentage_7d_in_currency || 0),
      mc: +c.market_cap || 0,
      vol24: +c.total_volume || 0,
      dominance: ((+c.market_cap||0)/sumMc)*100,
      spark7: (c.sparkline_in_7d && Array.isArray(c.sparkline_in_7d.price)) ? c.sparkline_in_7d.price : [],
      athDraw: (typeof c.ath_change_percentage==='number') ? Math.abs(c.ath_change_percentage) : null
    }));
    res.status(200).json({ list, vs, limit });
  }catch(e){
    res.status(500).json({ error: String(e) });
  }
}
