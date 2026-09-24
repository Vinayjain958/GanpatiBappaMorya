import { Minus, TrendingDown, TrendingUp } from "lucide-react";
import type { ProviderInsightStat } from "@/types/provider";
import { Card, CardBody } from "@/components/ui/Card";
import { cn } from "@/lib/utils/cn";

const trendIcon = { up: TrendingUp, down: TrendingDown, flat: Minus };

export function InsightStatCard({ stat }: { stat: ProviderInsightStat }) {
  const TrendIcon = stat.trend ? trendIcon[stat.trend] : null;

  return (
    <Card>
      <CardBody className="space-y-1.5">
        <p className="text-xs font-medium text-ink-subtle">{stat.label}</p>
        <p className="text-2xl font-semibold text-ink">{stat.value}</p>
        {stat.changeLabel ? (
          <p
            className={cn(
              "inline-flex items-center gap-1 text-xs",
              stat.trend === "up" && "text-success",
              stat.trend === "down" && "text-danger",
              (!stat.trend || stat.trend === "flat") && "text-ink-subtle",
            )}
          >
            {TrendIcon ? <TrendIcon className="size-3.5" aria-hidden="true" /> : null}
            {stat.changeLabel}
          </p>
        ) : null}
      </CardBody>
    </Card>
  );
}
