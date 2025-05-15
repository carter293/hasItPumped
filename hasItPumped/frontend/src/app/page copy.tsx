"use client"

import { useState, useEffect, useRef } from "react"
import Image from 'next/image'
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Toaster, toast, } from "sonner"
import { useQuery } from "@tanstack/react-query"
import { Search, ChevronRight, Loader2 } from "lucide-react"
import GeckoChart from "@/components/GeckoChart"
import { CoinInfo } from "@/components/CoinInfo"
import Link from "next/link"
import { StatsSection } from "@/components/StatsSection"
import { RecentTokensSection } from "@/components/RecentTokensSection"

// Define types for tokens
interface TokenDataPoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}
// Format large numbers with K, M suffixes
export const formatNumber = (num: number) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  }
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toFixed(2)
}

export interface TokenResponse {
  mint_address: string
  data: TokenDataPoint[]
  is_pre_peak: boolean
  confidence: number
  days_of_data: number
}

export interface TokenMetadata {
  name: string
  symbol: string
  poolAddress: string
  imageUrl: string
}

export interface TokenSummary {
  mint_address: string
  last_updated: string
  is_pre_peak: boolean
  current_price: number
  days_of_data: number
  volume_24h: number
}

export interface DatabaseStats {
  total_tokens: number
  pre_peak_count: number
  post_peak_count: number
  recent_tokens: TokenSummary[]
}


export default function Home() {
  const [mintAddress, setMintAddress] = useState("")
  const [activeToken, setActiveToken] = useState<TokenResponse | null>(null)
  const [meta, setMeta] = useState<TokenMetadata | null>(null);
  const [loading, setLoading] = useState(false)
  const [metaLoading, setMetaLoading] = useState(false)
  const resultRef = useRef<HTMLDivElement>(null)

  // Fetch stats for the dashboard
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const url = `${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}/stats`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch stats');
      return res.json();
    },
  });

  // Function to analyze token (unchanged)
  async function analyzeToken(address: string) {
    if (!address.trim()) {
      toast.error("Please enter a mint address")
      return
    }
    setMeta(null)
    setLoading(true)

    // Scroll to result area immediately to show loading state
    setTimeout(() => {
      if (resultRef.current) {
        resultRef.current.scrollIntoView({ behavior: 'smooth' })
      }
    }, 100)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/analyze_token`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ mint_address: address }),
      })

      if (!response.ok) {
        const error = await response.json()
        if (error.detail?.includes("not found") || error.detail?.includes("insufficient data")) {
          toast.error("This token hasn't been tracked long enough. We need more historical data.", {
            description: "Try analyzing a more established token."
          })
        } else if (error.detail?.includes("BitQuery")) {
          toast.error(`Could not retrieve data for mint_address: ${address}`)
        } else {
          toast.error(`${error.detail}` || "Failed to analyze token")
        }
        setActiveToken(null)
      } else {
        const data = await response.json()
        setActiveToken(data)
        refetchStats()
      }
    } catch (error) {
      console.error(error)
      setActiveToken(null)
    } finally {
      setLoading(false)
    }
  }

  // Load token metadata (unchanged)
  useEffect(() => {
    async function loadTokenMetadata() {
      if (!activeToken?.mint_address) return;

      setMetaLoading(true)
      try {
        const res = await fetch(
          `https://api.geckoterminal.com/api/v2/networks/solana/tokens/${activeToken?.mint_address}/`,
          { headers: { accept: 'application/json' } }
        );

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const json = await res.json();
        const { name, symbol, image_url } = json.data.attributes
        const poolAddressId = json.data.relationships.top_pools?.data[0]?.id
        const poolAddress = poolAddressId?.split('solana_')[1]
        
        if (!poolAddress) {
          toast.error('No pool found');
        } else if (name && symbol && image_url && poolAddress) {
          setMeta({ name, symbol, imageUrl: image_url, poolAddress })
        }
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Unexpected error fetching token metadata"
        toast.error(errorMessage);
      } finally {
        setMetaLoading(false)
      }
    }

    loadTokenMetadata();
  }, [activeToken]);

  const showLoadingSkeleton = loading || !activeToken || !meta || metaLoading 
  const showAnalysisSection = loading || activeToken
  
  return (
    <div className="flex min-h-screen flex-col bg-stone-900 text-white">
      {/* Toast container */}
      <div><Toaster position="top-center" richColors /></div>

      {/* Hero section - Made more mobile-friendly */}
      <section className="w-full bg-stone-900">
        <div className="container px-4 py-10 md:py-16 max-w-5xl mx-auto text-center flex-col justify-center items-center">
          <Image
            className="mx-auto w-32 h-32 md:w-48 md:h-48"
            src="/pumped.png"
            width={150}
            height={150}
            alt="has it pumped logo"
          />
          <h1 className="text-3xl md:text-5xl font-bold mb-3 md:mb-4">has it pumped?</h1>
          <p className="text-base md:text-lg mb-6 md:mb-8 max-w-2xl mx-auto opacity-90">
            analyze <span className="italic">*graduated</span> <Link target="_blank" href={"https://pump.fun"}> pump.fun</Link> solana tokens and predict if they&apos;ve already peaked or still have room to grow
          </p>

          <div className="w-full max-w-md mx-auto">
            <div className="flex flex-col sm:flex-row gap-2">
              <div className="relative flex-grow">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="enter solana token mint address"
                  className="pl-10 bg-white/10 border-white/20 text-white placeholder:text-gray-300 h-12 rounded-md w-full"
                  value={mintAddress}
                  onChange={(e) => setMintAddress(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      analyzeToken(mintAddress);
                    }
                  }}
                />
              </div>
              <Button
                onClick={() => analyzeToken(mintAddress)}
                disabled={loading}
                className="h-12 px-6 bg-green-500 hover:bg-green-600 text-white rounded-md sm:w-auto w-full"
              >
                {loading ? 'analyzing...' : 'analyze'}
              </Button>
            </div>
          </div>
        </div>
      </section>

      <section className="w-full bg-stone-900">
        <div className="container px-4 max-w-5xl mx-auto">

          {/* Token Analysis Result */}
          <div ref={resultRef}>
            {/* Show analysis section when loading or when we have token data */}
            {(showAnalysisSection) && (
              <>
                <h2 className="text-2xl font-bold mb-4 md:mb-6 text-white">token analysis</h2>
                <Card className="bg-zinc-800 border-gray-700 overflow-hidden">
                  {/* Show loading skeleton when loading, otherwise show CoinInfo */}
                  { showLoadingSkeleton ? (
                    <>
                      <CardHeader className="p-4">
                        <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
                          <div className="flex items-center gap-3">
                            <Skeleton className="h-16 w-16 bg-gray-700 rounded-md flex-shrink-0" /> {/* Token image */}
                            <div>
                              <Skeleton className="h-6 w-32 bg-gray-700 mb-2" /> {/* Token name */}
                              <Skeleton className="h-4 w-20 bg-gray-700 mb-1" /> {/* Token symbol */}
                              <Skeleton className="h-3 w-28 bg-gray-700" /> {/* Token address */}
                            </div>
                          </div>
                          <div className="mt-2 md:mt-0 md:text-right">
                            <Skeleton className="h-8 w-32 md:w-48 bg-gray-700 rounded-full mb-1 mx-auto md:ml-auto" /> {/* Status badge */}
                            <Skeleton className="h-4 w-24 bg-gray-700 mx-auto md:ml-auto" /> {/* Confidence */}
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent className="p-4">
                        <div className="space-y-6">
                          {/* Chart loading skeleton - matching the iframe dimensions */}
                          <div className="relative w-full rounded-lg border border-gray-700" style={{ height: window.innerWidth < 640 ? '300px' : '500px' }}>
                            <div className="absolute inset-0 bg-zinc-700/30 rounded-lg flex flex-col items-center justify-center">
                              <Loader2 className="h-12 w-12 text-gray-500 animate-spin mb-4" />
                              <div className="text-gray-400 text-sm">Loading chart data...</div>

                              {/* Simulated chart skeleton with gradient lines */}
                              <div className="absolute inset-0 overflow-hidden opacity-20">
                                <div className="w-full h-full flex flex-col justify-end">
                                  <div className="h-1/2 w-full relative">
                                    <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gray-400 to-transparent"></div>
                                    <div className="absolute bottom-1/4 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gray-400 to-transparent"></div>
                                    <div className="absolute bottom-2/4 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gray-400 to-transparent"></div>
                                    <div className="absolute bottom-3/4 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gray-400 to-transparent"></div>
                                    <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gray-400 to-transparent"></div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>

                          {/* Analysis summary loading skeleton */}
                          <div className="p-4 rounded-lg bg-stone-900/50 border border-gray-700">
                            <Skeleton className="h-5 w-40 bg-gray-700 mb-3" />
                            <Skeleton className="h-4 w-full bg-gray-700 mb-2" />
                            <Skeleton className="h-4 w-3/4 bg-gray-700 mb-2" />
                            <Skeleton className="h-4 w-full bg-gray-700" />
                          </div>
                        </div>
                      </CardContent>
                      <CardFooter className="justify-between border-t border-gray-700 p-4">
                        <Skeleton className="h-9 w-36 bg-gray-700 rounded" />
                        <Skeleton className="h-5 w-32 bg-gray-700" />
                      </CardFooter>
                    </>
                  ) : (
                    <>
                      <CoinInfo activeToken={activeToken} metadata={meta} />
                      <CardContent className="p-4">
                        <GeckoChart poolAddress={meta.poolAddress} />
                        <div className="mt-6 p-4 rounded-lg bg-stone-900/50 border border-gray-700">
                          <h4 className="font-medium mb-2 text-white">analysis summary</h4>
                          <p className="text-gray-300 text-sm md:text-base">
                            this token appears to be <strong>{activeToken?.is_pre_peak ? "pre-peak" : "post-peak"}</strong>.
                            {activeToken?.is_pre_peak
                              ? " the model predicts it has not reached its maximum price yet and may have potential for future growth."
                              : " the model predicts it has already reached its peak price and may not return to previous highs."
                            }
                          </p>
                          <p className="text-xs md:text-sm text-gray-500 mt-2">
                            note: this is an algorithmic prediction based on historical patterns and should not be considered financial advice.
                          </p>
                        </div>
                      </CardContent>
                      <CardFooter className="justify-between border-t border-gray-700 p-4">
                        <Button
                          variant="outline"
                          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                          className="bg-transparent border-gray-600 text-gray-300 text-sm"
                          disabled={loading}
                        >
                          analyze another
                        </Button>

                        {activeToken && (
                          <a
                            href={`https://solscan.io/token/${activeToken.mint_address}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-xs md:text-sm text-gray-400 transition-colors"
                          >
                            view on solscan
                            <ChevronRight className="ml-1 h-4 w-4" />
                          </a>
                        )}
                      </CardFooter>
                    </>
                  )}
                </Card>
              </>
            )}
          </div>

          {/* Stats section - Using our new StatsSection component */}
          <StatsSection stats={stats} statsLoading={statsLoading} />

          {/* Recent tokens - Using our new RecentTokensSection component */}
          <RecentTokensSection 
            tokens={stats?.recent_tokens} 
            loading={statsLoading} 
            analyzeToken={analyzeToken} 
          />
        </div>
      </section>

      {/* Footer */}
      <footer className="w-full mt-12 md:mt-20 py-6 bg-stone-900 text-gray-400">
        <div className="container px-4 max-w-5xl mx-auto text-center">
          <p className="text-sm">
            has it pumped yet? - solana token analysis tool
          </p>
          <p className="text-xs mt-2">
            this tool provides analysis based on historical patterns and should not be considered financial advice.
          </p>
        </div>
      </footer>

      {/* Global styles */}
      <style jsx global>{`
        html {
          scroll-behavior: smooth;
        }
        
        body {
          background-color: #000;
          color: #fff;
        }
        
        @media (max-width: 640px) {
          /* Additional mobile-specific styles */
          .container {
            padding-left: 12px;
            padding-right: 12px;
          }
        }
      `}</style>
    </div>
  )
}