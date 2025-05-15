import { DatabaseStats } from "@/app/page";
import { Skeleton } from "./ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Progress } from "@radix-ui/react-progress";
import { PieChart, TrendingDown, TrendingUp } from "lucide-react";

interface StatsSectionProps {
    stats: DatabaseStats;
    statsLoading: boolean;
}
export const StatsSection = ({ stats, statsLoading }: StatsSectionProps) => {
    return (
      <>
        <h2 className="text-2xl font-bold mb-4 mt-8 text-white">stats</h2>
  
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {statsLoading ? (
            <>
              <Skeleton className="h-28 bg-zinc-800 rounded-lg" />
              <Skeleton className="h-28 bg-zinc-800 rounded-lg" />
              <Skeleton className="h-28 bg-zinc-800 rounded-lg" />
            </>
          ) : (
            <>
              <Card className="bg-zinc-800 border-gray-700">
                <CardHeader className="pb-2 px-4 pt-4">
                  <CardTitle className="text-lg text-white">total tokens</CardTitle>
                </CardHeader>
                <CardContent className="px-4 pb-4">
                  <p className="text-2xl sm:text-3xl font-bold text-white">{stats?.total_tokens || 0}</p>
                  <div className="mt-2 flex items-center text-xs sm:text-sm text-gray-400">
                    <PieChart className="mr-1 h-4 w-4" />
                    <span>tokens analyzed in database</span>
                  </div>
                </CardContent>
              </Card>
  
              <Card className="bg-zinc-800 border-gray-700">
                <CardHeader className="pb-2 px-4 pt-4">
                  <CardTitle className="text-lg text-white">pre-pump tokens</CardTitle>
                </CardHeader>
                <CardContent className="px-4 pb-4">
                  <p className="text-2xl sm:text-3xl font-bold text-green-400">
                    {stats?.pre_peak_count || 0}
                  </p>
                  <Progress
                    value={stats ? (stats.pre_peak_count / Math.max(1, stats.total_tokens) * 100) : 0}
                    className="mt-2 bg-gray-700 h-2"
                  />
                  <div className="mt-2 flex items-center text-xs sm:text-sm text-gray-400">
                    <TrendingUp className="mr-1 h-4 w-4 text-green-400" />
                    <span>still have potential for growth</span>
                  </div>
                </CardContent>
              </Card>
  
              <Card className="bg-zinc-800 border-gray-700 sm:col-span-2 lg:col-span-1">
                <CardHeader className="pb-2 px-4 pt-4">
                  <CardTitle className="text-lg text-white">pumped tokens</CardTitle>
                </CardHeader>
                <CardContent className="px-4 pb-4">
                  <p className="text-2xl sm:text-3xl font-bold text-red-400">
                    {stats?.post_peak_count || 0}
                  </p>
                  <Progress
                    value={stats ? (stats.post_peak_count / Math.max(1, stats.total_tokens) * 100) : 0}
                    className="mt-2 bg-gray-700 h-2"
                  />
                  <div className="mt-2 flex items-center text-xs sm:text-sm text-gray-400">
                    <TrendingDown className="mr-1 h-4 w-4 text-red-400" />
                    <span>already reached their peak</span>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </>
    );
  };