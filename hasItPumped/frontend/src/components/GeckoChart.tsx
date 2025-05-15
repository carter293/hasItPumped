'use client';

import { useEffect, useState } from 'react';

type Props = {
  poolAddress: string;
};

export default function GeckoChart({ poolAddress }: Props) {
  const [chartHeight, setChartHeight] = useState(600);
  
  // Adjust chart height based on screen size
  useEffect(() => {
    const updateChartHeight = () => {
      // For mobile screens, use a shorter height
      if (window.innerWidth < 640) {
        setChartHeight(400);
      } else if (window.innerWidth < 1024) {
        setChartHeight(500);
      } else {
        setChartHeight(600);
      }
    };
    
    // Initial check
    updateChartHeight();
    
    // Add resize listener
    window.addEventListener('resize', updateChartHeight);
    
    // Cleanup
    return () => window.removeEventListener('resize', updateChartHeight);
  }, []);

  const src = `https://www.geckoterminal.com/solana/pools/${poolAddress}` +
              `?embed=1&info=0&swaps=0&grayscale=0&light_chart=0` +
              `&chart_type=price&resolution=15m&theme=dark`;

  return (
    <div className="w-full overflow-hidden rounded-lg border border-gray-700">
      <iframe
        id="geckoterminal-embed"
        title="GeckoTerminal Chart"
        src={src}
        width="100%"
        height={chartHeight}
        allow="clipboard-write"
        allowFullScreen
        className="w-full"
      />
    </div>
  );
}