/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-064 v1.2.0: Harita katman registery'si + THERMAL_STRESS katmani. */
/* KR-084 v1.2.0: Termal stres katmani (Dark Red/Orange gradient + termometre ikonu). */

'use client';

import { useState, useCallback } from 'react';

import type { ResultLayer } from '../services/resultService';

/** KR-064: Kanonik harita katman tanimlari. */
const LAYER_CONFIG: Record<string, { label: string; color: string; icon: string; priority: number }> = {
  HEALTH: { label: 'Genel Saglik', color: '#22c55e', icon: '🟢', priority: 1 },
  DISEASE: { label: 'Hastalik', color: '#f97316', icon: '🟠', priority: 2 },
  PEST: { label: 'Zararli', color: '#ef4444', icon: '🔴', priority: 3 },
  FUNGUS: { label: 'Mantar', color: '#a855f7', icon: '🟣', priority: 4 },
  WEED: { label: 'Yabanci Ot', color: '#eab308', icon: '🟡', priority: 5 },
  WATER_STRESS: { label: 'Su Stresi', color: '#3b82f6', icon: '💧', priority: 6 },
  N_STRESS: { label: 'Azot Stresi', color: '#6b7280', icon: '⬛', priority: 7 },
  // KR-064/KR-084 v1.2.0: Yeni termal stres katmani
  THERMAL_STRESS: { label: 'Termal Stres / Sulama', color: '#dc2626', icon: '🌡️', priority: 8 },
};

interface LayerListProps {
  readonly layers: readonly ResultLayer[];
  readonly onToggle?: (layerName: string, visible: boolean) => void;
}

export function LayerList({ layers, onToggle }: LayerListProps) {
  const [visibility, setVisibility] = useState<Record<string, boolean>>(() => {
    const init: Record<string, boolean> = {};
    for (const layer of layers) {
      init[layer.layerName] = true;
    }
    return init;
  });

  const handleToggle = useCallback(
    (layerName: string) => {
      setVisibility((prev) => {
        const next = { ...prev, [layerName]: !prev[layerName] };
        onToggle?.(layerName, next[layerName]);
        return next;
      });
    },
    [onToggle]
  );

  const sorted = [...layers].sort((a, b) => {
    const pa = LAYER_CONFIG[a.layerType]?.priority ?? 99;
    const pb = LAYER_CONFIG[b.layerType]?.priority ?? 99;
    return pa - pb;
  });

  return (
    <ul role="list" aria-label="Analiz katmanlari">
      {sorted.map((layer) => {
        const config = LAYER_CONFIG[layer.layerType];
        const isVisible = visibility[layer.layerName] ?? true;

        return (
          <li key={layer.layerName} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '4px 0' }}>
            <input
              type="checkbox"
              checked={isVisible}
              onChange={() => handleToggle(layer.layerName)}
              aria-label={`${config?.label ?? layer.layerType} katmanini goster/gizle`}
            />
            <span
              style={{
                width: 12,
                height: 12,
                borderRadius: '50%',
                backgroundColor: config?.color ?? '#999',
                display: 'inline-block',
              }}
            />
            <span>{config?.label ?? layer.layerType}</span>
          </li>
        );
      })}
    </ul>
  );
}
