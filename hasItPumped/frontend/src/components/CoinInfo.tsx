import { Link as Llink } from "lucide-react"
import Image from 'next/image'
import Link from "next/link"
import { TokenMetadata, TokenResponse } from "@/app/page"
import { CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

interface CoinInfoProps {
    activeToken: TokenResponse
    metadata: TokenMetadata
}

export const CoinInfo = ({ activeToken, metadata }: CoinInfoProps) => {
        return (
          <CardHeader className="px-3 sm:px-6">
            <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
              {/* Left side - Token info */}
              <div className="flex items-center gap-3">
                {/* Image with proper responsive size */}
                <div className="flex-shrink-0">
                  <Image 
                    src={`${metadata.imageUrl}?img-width=256`} 
                    width={64} 
                    height={64} 
                    alt={metadata.name || 'Token image'} 
                    className="rounded-md"
                  />
                </div>
                
                {/* Token name and details */}
                <div>
                  <CardTitle className="font-mono text-xl text-white">
                    {metadata.name}
                  </CardTitle>
                  <CardDescription className="text-gray-400 flex flex-col gap-1">
                    <div className="text-sm">${metadata.symbol}</div>
                    <Link 
                      target="_blank" 
                      href={`https://pump.fun/coin/${activeToken.mint_address}`} 
                      className="flex items-center gap-1 text-xs overflow-hidden"
                    >
                      <Llink size={12} />
                      <span className="truncate max-w-[150px] sm:max-w-[220px] md:max-w-full">
                        {activeToken.mint_address}
                      </span>
                    </Link>
                  </CardDescription>
                </div>
              </div>
              
              {/* Right side - Pump status */}
              <div className="md:text-right mt-2 md:mt-0">
                <span 
                  className={`inline-flex items-center justify-center rounded-full px-3 py-1 text-sm md:text-base font-medium whitespace-nowrap
                    ${activeToken.is_pre_peak
                      ? "bg-green-900/60 text-green-300 border border-green-500/30"
                      : "bg-red-900/60 text-red-300 border border-red-500/30"
                    }`}
                >
                  <span className="font-bold">
                    {activeToken.is_pre_peak ? "PRE-PUMP" : "POST-PUMP"}
                  </span>
                </span>
                <p className="text-xs sm:text-sm text-gray-400 mt-1">
                  {Math.round(activeToken.confidence * 100)}% Confident
                </p>
              </div>
            </div>
          </CardHeader>
        );
      }