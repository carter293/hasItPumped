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
        <CardHeader>
            <div className="flex justify-between items-center">
                <div>
                    <Image src={`${metadata.imageUrl}?img-width=256`} width={100} height={100} alt={''} />
                    <CardTitle className="font-mono text-xl mb-2 mt-2 text-white">
                        {metadata.name}
                    </CardTitle>
                    <CardDescription className="text-gray-400 flex-col">
                        <div>${metadata.symbol}</div>
                        <Link target="_blank" href={`https://pump.fun/coin/${activeToken.mint_address}`} className='flex gap-2 items-center justify-center align-middle'>
                            <Llink size={15} /> {activeToken.mint_address}
                        </Link>
                    </CardDescription>
                </div>
                <div className="text-right">
                    <span className={`inline-flex items-center gap-1 justify-center rounded-full px-5 py-1 text-l font-medium ${activeToken.is_pre_peak
                        ? "bg-green-900/60 text-green-300 border border-green-500/30"
                        : "bg-red-900/60 text-red-300 border border-red-500/30"
                        }`}>
                        <span className="text-2xl italic font-extrabold">Coin {activeToken.is_pre_peak ? " is PRE PUMP" : " has PUMPED"}</span>
                    </span>
                    <p className="text-sm text-gray-400 mt-1">
                        {Math.round(activeToken.confidence * 100)}% Confident
                    </p>
                </div>
            </div>
        </CardHeader>
    )
}