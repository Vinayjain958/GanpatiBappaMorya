"use client";

import React, { useEffect, useState } from "react";
import { getProviderInsights, getProviderNotifications, markNotificationRead } from "@/lib/api/providers";
import type { ProviderInsightResponse, ProviderNotificationListResponse } from "@/types/provider-intelligence";
import { Activity, BarChart3, Clock, TrendingUp, Users } from "lucide-react";

export function ProviderInsightsDashboard() {
  const [insights, setInsights] = useState<ProviderInsightResponse | null>(null);
  const [notifications, setNotifications] = useState<ProviderNotificationListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [windowState, setWindowState] = useState("30d");

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [resInsights, resNotif] = await Promise.all([
          getProviderInsights(windowState),
          getProviderNotifications(false)
        ]);
        setInsights(resInsights);
        setNotifications(resNotif);
      } catch (err) {
        console.error("Failed to load provider insights", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [windowState]);

  if (loading) {
    return <div className="p-8 text-center text-ink-muted">Loading intelligence data...</div>;
  }

  if (!insights) {
    return <div className="p-8 text-center text-ink-muted">Failed to load data.</div>;
  }

  return (
    <div className="space-y-8">
      {/* Window Selector */}
      <div className="flex gap-2">
        {["7d", "30d", "90d"].map(w => (
          <button 
            key={w} 
            onClick={() => setWindowState(w)}
            className={`px-4 py-2 rounded ${windowState === w ? "bg-primary text-white" : "bg-surface-sunken"}`}
          >
            {w}
          </button>
        ))}
      </div>

      {insights.provenance.has_synthetic_data && (
        <div className="bg-amber-100 text-amber-900 p-4 rounded-md font-medium text-sm">
          Contains pre-aggregated synthetic data for demonstration.
        </div>
      )}

      {/* KPIs */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-line bg-surface p-4">
          <div className="text-sm font-medium text-ink-muted mb-1">Views</div>
          <div className="text-2xl font-semibold">{insights.kpis.views}</div>
        </div>
        <div className="rounded-lg border border-line bg-surface p-4">
          <div className="text-sm font-medium text-ink-muted mb-1">Saves</div>
          <div className="text-2xl font-semibold">{insights.kpis.saves}</div>
        </div>
        <div className="rounded-lg border border-line bg-surface p-4">
          <div className="text-sm font-medium text-ink-muted mb-1">Booking Requests</div>
          <div className="text-2xl font-semibold">{insights.kpis.booking_requests}</div>
        </div>
        <div className="rounded-lg border border-line bg-surface p-4">
          <div className="text-sm font-medium text-ink-muted mb-1">Accepted</div>
          <div className="text-2xl font-semibold">{insights.kpis.accepted_bookings}</div>
        </div>
      </div>

      {/* Segments */}
      <div className="rounded-lg border border-line bg-surface p-6">
        <h3 className="text-lg font-medium mb-4">Traveler Interest Segments</h3>
        <div className="space-y-3">
          {insights.segments.map((seg, idx) => (
            <div key={idx} className="flex justify-between items-center text-sm">
              <span className="font-medium">{seg.label} <span className="text-ink-muted text-xs">({seg.segment_type})</span></span>
              <span>
                {seg.minimum_sample_met ? (
                  `${(seg.share! * 100).toFixed(1)}% (${seg.interactions} interactions)`
                ) : (
                  <span className="text-ink-muted italic">Insufficient data</span>
                )}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Notifications */}
      {notifications && notifications.items.length > 0 && (
        <div className="rounded-lg border border-line bg-surface p-6">
          <h3 className="text-lg font-medium mb-4">Recent Match & Booking Alerts</h3>
          <div className="space-y-4">
            {notifications.items.map(n => (
              <div key={n.id} className={`flex justify-between items-start p-4 rounded-md ${n.is_read ? 'bg-surface-sunken opacity-70' : 'bg-primary/10 border border-primary/20'}`}>
                <div>
                  <h4 className="font-semibold text-sm">{n.title}</h4>
                  <p className="text-sm text-ink-muted mt-1">{n.body}</p>
                  {n.segment_summary && (
                    <div className="mt-2 flex gap-2 flex-wrap">
                      {n.segment_summary.map((s, idx) => (
                        <span key={idx} className="text-xs bg-surface-sunken px-2 py-1 rounded">{s}</span>
                      ))}
                    </div>
                  )}
                  {n.booking_request_id && (
                    <div className="mt-2 text-xs font-mono text-ink-muted">Ref: {n.booking_request_id}</div>
                  )}
                </div>
                {!n.is_read && (
                  <button 
                    onClick={async () => {
                      await markNotificationRead(n.id);
                      setNotifications(prev => prev ? {
                        ...prev, 
                        items: prev.items.map(x => x.id === n.id ? {...x, is_read: true} : x)
                      } : prev);
                    }}
                    className="text-xs text-primary font-medium hover:underline"
                  >
                    Mark Read
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
