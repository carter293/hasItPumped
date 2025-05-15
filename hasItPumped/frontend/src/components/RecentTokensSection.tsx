import { formatNumber, TokenSummary } from "@/app/page";
import { Skeleton } from "./ui/skeleton";
import { Button } from "./ui/button";
import { AlertCircle } from "lucide-react";

interface RecentTokensSectionProps {
  tokens: TokenSummary[];
  loading: boolean;
  analyzeToken: (address: string) => Promise<void>;
}
// This component will replace the Recent Tokens table in your Home component
export const RecentTokensSection = ({ tokens, loading, analyzeToken }: RecentTokensSectionProps) => {
    return (
      <>
        <h3 className="text-xl font-bold mt-10 mb-4 text-white">recent tokens</h3>
        
        {/* Desktop Table (hidden on mobile) */}
        <div className="hidden md:block overflow-x-auto rounded-lg border border-gray-700">
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
              {loading ? (
                Array(5).fill(0).map((_, i) => (
                  <tr key={i} className="border-b border-gray-700">
                    <td colSpan={7} className="py-3 px-4"><Skeleton className="h-6 bg-gray-700" /></td>
                  </tr>
                ))
              ) : tokens?.length ? (
                tokens.map((token) => (
                  <tr
                    key={token.mint_address}
                    className="border-b border-gray-700 hover:bg-gray-700/50 transition-colors"
                  >
                    <td className="py-3 px-4 font-mono text-xs text-gray-300">
                      {token.mint_address.substring(0, 8)}...{token.mint_address.substring(token.mint_address.length - 8)}
                    </td>
                    <td className="py-3 px-4 text-gray-300">{new Date(token.last_updated).toLocaleDateString()}</td>
                    <td className="py-3 px-4">
                      <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                        token.is_pre_peak
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
        
        {/* Mobile Card View */}
        <div className="md:hidden space-y-3">
          {loading ? (
            Array(3).fill(0).map((_, i) => (
              <div key={i} className="rounded-lg border border-gray-700 p-4">
                <Skeleton className="h-6 w-2/3 bg-gray-700 mb-2" />
                <Skeleton className="h-6 w-full bg-gray-700 mb-2" />
                <Skeleton className="h-6 w-1/2 bg-gray-700" />
              </div>
            ))
          ) : tokens?.length ? (
            tokens.map((token) => (
              <div
                key={token.mint_address}
                className="rounded-lg border border-gray-700 p-4 bg-zinc-800 hover:bg-zinc-700/90 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="font-mono text-xs text-gray-300 truncate max-w-[150px]">
                    {token.mint_address.substring(0, 6)}...{token.mint_address.substring(token.mint_address.length - 6)}
                  </div>
                  <div className="text-xs text-gray-400">
                    {new Date(token.last_updated).toLocaleDateString()}
                  </div>
                </div>
                
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                      token.is_pre_peak
                        ? "bg-green-900/60 text-green-300 border border-green-500/30"
                        : "bg-red-900/60 text-red-300 border border-red-500/30"
                    }`}>
                      {token.is_pre_peak ? "pre-pump" : "post-pump"}
                    </span>
                  </div>
                  <div className="text-gray-300 font-medium">${token.current_price.toFixed(6)}</div>
                </div>
                
                <div className="flex items-center justify-between text-xs mb-3">
                  <div className="text-gray-400">Volume (24h)</div>
                  <div className="text-gray-300">${formatNumber(token.volume_24h)}</div>
                </div>
                
                <div className="flex items-center justify-between text-xs mb-4">
                  <div className="text-gray-400">Days of data</div>
                  <div className="text-gray-300">{token.days_of_data}</div>
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    analyzeToken(token.mint_address);
                  }}
                  className="w-full bg-transparent border-gray-600 hover:bg-gray-700 text-gray-300"
                >
                  view details
                </Button>
              </div>
            ))
          ) : (
            <div className="rounded-lg border border-gray-700 p-6 flex flex-col items-center justify-center bg-zinc-800 text-gray-500">
              <AlertCircle className="h-8 w-8 mb-2" />
              <p>no tokens found in database</p>
            </div>
          )}
        </div>
      </>
    );
  };