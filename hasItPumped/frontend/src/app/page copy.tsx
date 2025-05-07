"use client"

import { useState, useEffect, useRef } from "react"
import Image from 'next/image'
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Toaster, toast, } from "sonner"
import { useQuery } from "@tanstack/react-query"
import { Search, PieChart, TrendingUp, TrendingDown, ChevronRight, AlertCircle } from "lucide-react"
import TokenChart from "@/components/TokenChart";

// Define types for tokens
interface TokenDataPoint {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface TokenResponse {
  mint_address: string
  data: TokenDataPoint[]
  is_pre_peak: boolean
  confidence: number
  days_of_data: number
}

interface TokenSummary {
  mint_address: string
  last_updated: string
  is_pre_peak: boolean
  current_price: number
  days_of_data: number
  volume_24h: number
}

interface DatabaseStats {
  total_tokens: number
  pre_peak_count: number
  post_peak_count: number
  recent_tokens: TokenSummary[]
}

export default function Home() {
  const [mintAddress, setMintAddress] = useState("")
  const [activeToken, setActiveToken] = useState<TokenResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [newlyAnalyzedToken, setNewlyAnalyzedToken] = useState<string | null>(null)
  const resultRef = useRef<HTMLDivElement>(null)
  const router = useRouter()

  // Fetch stats for the dashboard
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery<DatabaseStats>({
    queryKey: ['stats'],
    queryFn: async () => {
      const url = `${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}/stats`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Failed to fetch stats');
      return res.json();
    },
  });

  // Function to analyze token
  async function analyzeToken(address: string) {
    if (!address.trim()) {
      toast.error("Please enter a mint address")
      return
    }

    setLoading(true)
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
        } else {
          toast.error(`${error.detail}` || "Failed to analyze token")
        }
      } else {
        const data = await response.json()
        setActiveToken(data)
        setNewlyAnalyzedToken(data.mint_address)

        // Trigger stats refresh to include the newly analyzed token
        refetchStats()

        // Smooth scroll to results after a short delay
        setTimeout(() => {
          if (resultRef.current) {
            resultRef.current.scrollIntoView({ behavior: 'smooth' })
          }
        }, 100)
      }
    } catch (error: any) {
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  // Clear highlight effect after animation completes
  useEffect(() => {
    if (newlyAnalyzedToken) {
      const timer = setTimeout(() => {
        setNewlyAnalyzedToken(null)
      }, 3000)
      return () => clearTimeout(timer)
    }
  }, [newlyAnalyzedToken])

  // Format large numbers with K, M suffixes
  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M'
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K'
    }
    return num.toFixed(2)
  }

  // Calculate price change percentage
  const getPriceChange = (data: TokenDataPoint[] | undefined) => {
    if (!data || data.length < 2) return { value: 0, isPositive: true }

    const current = data[0].close
    const previous = data[1].close
    const change = ((current - previous) / previous) * 100

    return {
      value: Math.abs(change).toFixed(2),
      isPositive: change >= 0
    }
  }

  // Skeleton for chart
  const ChartSkeleton = () => (
    <div className="w-full h-48 flex items-end space-x-0.5">
      {Array(30).fill(0).map((_, i) => (
        <div key={i} className="flex-1 h-full relative">
          <Skeleton className="w-full absolute bottom-0 bg-gray-200" style={{ height: `${Math.random() * 70 + 10}%` }} />
        </div>
      ))}
    </div>
  )

  return (
    <div className="flex min-h-screen flex-col bg-black text-white">
      {/* Toast container */}
      <div><Toaster position="top-center" richColors /></div>

      {/* Hero section */}
      <section className="w-full bg-stone-900">
        <div className="container px-4 py-16 md:py-24 max-w-5xl mx-auto text-center flex-col justify-center items-center">
          <Image
            className=" mx-auto"
            src="/pumped.png"
            width={200}
            height={200}
            alt="Picture of the author"
          />
          <h1 className="text-4xl md:text-6xl font-bold mb-4">has it pumped?</h1>
          <p className="text-lg md:text-xl mb-8 max-w-2xl mx-auto opacity-90">
            analyze solana tokens and predict if they've already peaked or still have room to grow
          </p>

          <div className="max-w-md mx-auto">
            <div className="flex space-x-2">
              <div className="relative flex-grow">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="enter solana token mint address"
                  className="pl-10 bg-white/10 border-white/20 text-white placeholder:text-gray-300 h-12 rounded-md"
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
                className="h-12 px-6 bg-green-500 hover:bg-green-600 text-white rounded-md"
              >
                {loading ? 'analyzing...' : 'analyze'}
              </Button>
            </div>
          </div>
        </div>
      </section>

      <section className="w-full py-12 bg-stone-900">
        <div className="container px-4 max-w-5xl mx-auto">
          {/* Stats section */}
          <h2 className="text-2xl font-bold mb-6 text-white">stats</h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {statsLoading ? (
              <>
                <Skeleton className="h-32 bg-zinc-800" />
                <Skeleton className="h-32 bg-zinc-800" />
                <Skeleton className="h-32 bg-zinc-800" />
              </>
            ) : (
              <>
                <Card className="bg-zinc-800 border-gray-700">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg text-white">total tokens</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold text-white">{stats?.total_tokens || 0}</p>
                    <div className="mt-2 flex items-center text-sm text-gray-400">
                      <PieChart className="mr-1 h-4 w-4" />
                      <span>tokens analyzed in database</span>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-zinc-800 border-gray-700">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg text-white">pre-pump tokens</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold text-green-400">
                      {stats?.pre_peak_count || 0}
                    </p>
                    <Progress
                      value={stats ? (stats.pre_peak_count / Math.max(1, stats.total_tokens) * 100) : 0}
                      className="mt-2 bg-gray-700"
                    />
                    <div className="mt-2 flex items-center text-sm text-gray-400">
                      <TrendingUp className="mr-1 h-4 w-4 text-green-400" />
                      <span>still have potential for growth</span>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-zinc-800 border-gray-700">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg text-white">pumped tokens</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-3xl font-bold text-red-400">
                      {stats?.post_peak_count || 0}
                    </p>
                    <Progress
                      value={stats ? (stats.post_peak_count / Math.max(1, stats.total_tokens) * 100) : 0}
                      className="mt-2 bg-gray-700"
                    />
                    <div className="mt-2 flex items-center text-sm text-gray-400">
                      <TrendingDown className="mr-1 h-4 w-4 text-red-400" />
                      <span>already reached their peak</span>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </div>

          {/* Token Analysis Result */}
          <div ref={resultRef}>
            {activeToken && (
              <>
                <h2 className="text-2xl font-bold mt-10 mb-6 text-white">token analysis</h2>
                <Card className="bg-zinc-800 border-gray-700 overflow-hidden">
                  <CardHeader>
                    <div className="flex justify-between items-center">
                      <div>
                        <CardTitle className="font-mono text-sm mb-2 text-white">
                          {activeToken.mint_address}
                        </CardTitle>
                        <CardDescription className="text-gray-400">
                          {activeToken.days_of_data} days of historical data
                        </CardDescription>
                      </div>
                      <div className="text-right">
                        <span className={`inline-flex items-center rounded-full px-3 py-1 text-l font-medium ${activeToken.is_pre_peak
                          ? "bg-green-900/60 text-green-300 border border-green-500/30"
                          : "bg-red-900/60 text-red-300 border border-red-500/30"
                          }`}>
                          {activeToken.is_pre_peak ? "PREPUMPED" : "PUMPED"}
                        </span>
                        <p className="text-sm text-gray-400 mt-1">
                          {Math.round(activeToken.confidence * 100)}% confidence
                        </p>
                      </div>
                    </div>
                  </CardHeader>

                  <CardContent>
                    <Tabs defaultValue="chart" className="text-white">
                      <TabsList className="bg-gray-700">
                        <TabsTrigger
                          value="chart"
                          className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white"
                        >
                          chart
                        </TabsTrigger>
                        <TabsTrigger
                          value="data"
                          className="data-[state=active]:bg-zinc-800 data-[state=active]:text-white"
                        >
                          data
                        </TabsTrigger>
                      </TabsList>

                      <TabsContent value="chart" className="pt-4">
                        {loading ? (
                          <ChartSkeleton />
                        ) : activeToken.data && (
                          <>
                            <div className="flex justify-between items-center mb-4">
                              <div>
                                <p className="text-2xl font-bold text-white">
                                  ${activeToken.data[0].close.toFixed(6)}
                                </p>
                                <div className="flex items-center mt-1">
                                  {(() => {
                                    const change = getPriceChange(activeToken.data);
                                    return (
                                      <span className={`flex items-center text-sm ${change.isPositive ? "text-green-400" : "text-red-400"
                                        }`}>
                                        {change.isPositive ? <TrendingUp className="mr-1 h-4 w-4" /> : <TrendingDown className="mr-1 h-4 w-4" />}
                                        {change.value}%
                                      </span>
                                    );
                                  })()}
                                  <span className="text-xs text-gray-400 ml-2">24h change</span>
                                </div>
                              </div>
                              <div className="text-right">
                                <p className="text-sm font-semibold text-gray-300">volume (24h)</p>
                                <p className="text-white">${formatNumber(activeToken.data[0].volume)}</p>
                              </div>
                            </div>

                            <TokenChart data={activeToken.data} loading={loading} />

                            <div className="mt-6 p-4 rounded-lg bg-stone-900/50 border border-gray-700">
                              <h4 className="font-medium mb-2 text-white">analysis summary</h4>
                              <p className="text-gray-300">
                                this token appears to be <strong>{activeToken.is_pre_peak ? "pre-peak" : "post-peak"}</strong>.
                                {activeToken.is_pre_peak
                                  ? " the model predicts it has not reached its maximum price yet and may have potential for future growth."
                                  : " the model predicts it has already reached its peak price and may not return to previous highs."
                                }
                              </p>
                              <p className="text-sm text-gray-500 mt-2">
                                note: this is an algorithmic prediction based on historical patterns and should not be considered financial advice.
                              </p>
                            </div>
                          </>
                        )}
                      </TabsContent>

                      <TabsContent value="data" className="pt-4">
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-gray-700">
                                <th className="text-left py-2 px-4 text-gray-400">date</th>
                                <th className="text-right py-2 px-4 text-gray-400">open</th>
                                <th className="text-right py-2 px-4 text-gray-400">high</th>
                                <th className="text-right py-2 px-4 text-gray-400">low</th>
                                <th className="text-right py-2 px-4 text-gray-400">close</th>
                                <th className="text-right py-2 px-4 text-gray-400">volume</th>
                              </tr>
                            </thead>
                            <tbody>
                              {loading ? (
                                Array(5).fill(0).map((_, i) => (
                                  <tr key={i} className="border-b border-gray-700">
                                    <td colSpan={6} className="py-3 px-4"><Skeleton className="h-5 bg-gray-700" /></td>
                                  </tr>
                                ))
                              ) : (
                                activeToken.data.slice(0, 30).map((day) => (
                                  <tr key={day.date} className="border-b border-gray-700 transition-colors">
                                    <td className="py-2 px-4 text-gray-300">{new Date(day.date).toLocaleDateString()}</td>
                                    <td className="text-right py-2 px-4 text-gray-300">${day.open.toFixed(6)}</td>
                                    <td className="text-right py-2 px-4 text-gray-300">${day.high.toFixed(6)}</td>
                                    <td className="text-right py-2 px-4 text-gray-300">${day.low.toFixed(6)}</td>
                                    <td className="text-right py-2 px-4 text-gray-300">${day.close.toFixed(6)}</td>
                                    <td className="text-right py-2 px-4 text-gray-300">${formatNumber(day.volume)}</td>
                                  </tr>
                                ))
                              )}
                            </tbody>
                          </table>
                          {activeToken.data.length > 30 && (
                            <p className="text-center text-sm text-gray-500 mt-4">
                              showing first 30 days of {activeToken.data.length} total days
                            </p>
                          )}
                        </div>
                      </TabsContent>
                    </Tabs>
                  </CardContent>

                  <CardFooter className="justify-between border-t border-gray-700 pt-4">
                    <Button
                      variant="outline"
                      onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                      className="bg-transparent border-gray-600 text-gray-300"
                    >
                      analyze another token
                    </Button>

                    <a
                      href={`https://solscan.io/token/${activeToken.mint_address}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-sm text-gray-400transition-colors"
                    >
                      view on solscan
                      <ChevronRight className="ml-1 h-4 w-4" />
                    </a>
                  </CardFooter>
                </Card>
              </>
            )}
          </div>

          {/* Recent tokens */}
          <h3 className="text-xl font-bold mt-10 mb-4 text-white">recent tokens</h3>

          <div className="overflow-x-auto rounded-lg border border-gray-700">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-zinc-800 border-b border-gray-700">
                  <th className="text-left py-3 px-4 text-gray-400">token address</th>
                  <th className="text-left py-3 px-4 text-gray-400">last updated</th>
                  <th className="text-left py-3 px-4 text-gray-400">status</th>
                  <th className="text-left py-3 px-4 text-gray-400">current price</th>
                  <th className="text-left py-3 px-4 text-gray-400">volume (24h)</th>
                  <th className="text-left py-3 px-4 text-gray-400">days of data</th>
                  <th className="text-right py-3 px-4 text-gray-400">action</th>
                </tr>
              </thead>
              <tbody>
                {statsLoading ? (
                  Array(5).fill(0).map((_, i) => (
                    <tr key={i} className="border-b border-gray-700">
                      <td colSpan={7} className="py-3 px-4"><Skeleton className="h-6 bg-gray-700" /></td>
                    </tr>
                  ))
                ) : stats?.recent_tokens?.length ? (
                  stats.recent_tokens.map((token) => (
                    <tr
                      key={token.mint_address}
                      className={`border-b border-gray-700 hover:bg-gray-700/50 transition-colors`}
                    >
                      <td className="py-3 px-4 font-mono text-xs text-gray-300">
                        {token.mint_address.substring(0, 8)}...{token.mint_address.substring(token.mint_address.length - 8)}
                      </td>
                      <td className="py-3 px-4 text-gray-300">{new Date(token.last_updated).toLocaleDateString()}</td>
                      <td className="py-3 px-4">
                        <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${token.is_pre_peak
                          ? "bg-green-900/60 text-green-300 border border-green-500/30"
                          : "bg-red-900/60 text-red-300 border border-red-500/30"
                          }`}>
                          {token.is_pre_peak ? "pre-pump" : "post-pump"}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-gray-300">${token.current_price.toFixed(6)}</td>
                      <td className="py-3 px-4 text-gray-300">${formatNumber(token.volume_24h)}</td>
                      <td className="py-3 px-4 text-gray-300">{token.days_of_data}</td>
                      <td className="py-3 px-4 text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setMintAddress(token.mint_address);
                            analyzeToken(token.mint_address);
                          }}
                          className="bg-transparent border-gray-600 hover:bg-gray-700 text-gray-300"
                        >
                          view
                        </Button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="py-8 text-center">
                      <div className="flex flex-col items-center justify-center text-gray-500">
                        <AlertCircle className="h-8 w-8 mb-2" />
                        <p>no tokens found in database</p>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="w-full py-6 bg-gray-950 text-gray-400 mt-auto">
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
        
        .highlight-card {
          position: relative;
        }
        
        @keyframes flashBorder {
          0% { border-color: rgba(245, 158, 11, 0); }
          50% { border-color: rgba(245, 158, 11, 1); }
          100% { border-color: rgba(245, 158, 11, 0); }
        }
        
        .highlight-row {
          animation: flashBorder 2s ease-in-out;
        }
      `}</style>
    </div>
  )
}
