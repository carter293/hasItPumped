'use client';                           // <-- keep if you’re in Next.js “app/”  


type Props = {
    poolAddress: string;
};

export default function GeckoChart({ poolAddress }: Props) {
  const src = `https://www.geckoterminal.com/solana/pools/${poolAddress}` +
              `?embed=1&info=0&swaps=0&grayscale=0&light_chart=0` +
              `&chart_type=price&resolution=15m`;

  return (
    <iframe
      id="geckoterminal-embed"
      title="GeckoTerminal Chart"
      src={src}
      width="100%"
      height="100%"
      allow="clipboard-write"
      allowFullScreen
      style={{ minHeight: 600 }}
    />
  );
}