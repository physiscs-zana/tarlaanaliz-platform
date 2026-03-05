/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-064 v1.2.0: Harita katman registery'si + THERMAL_STRESS katmani. */
/* KR-084 v1.2.0: Termal stres katmani (Dark Red/Orange gradient + termometre ikonu). */

'use client';

import { useState, useCallback } from 'react';

import type { ResultLayer } from '../services/resultService';

/**
 * KR-064 v1.2.0: Kanonik harita katman tanimlari.
 * Priority, opacity, renk ve desen/ikon degerleri SSOT TARLAANALIZ_SSOT_v1_2_0.txt ile birebir eslesir.
 * Cakisma kurali: priority yuksek katman ustte gorunur. Erisilebilirlik icin ikon + desen zorunludur.
 */
const LAYER_CONFIG: Record<string, { label: string; color: string; icon: string; pattern: string; opacity: number; priority: number }> = {
  HEALTH:         { label: 'Genel Saglik',        color: '#22c55e', icon: 'leaf',        pattern: 'gradient-heatmap',  opacity: 0.55, priority: 10 },
  N_STRESS:       { label: 'Azot Stresi',         color: '#6b7280', icon: 'N',           pattern: 'crosshatch',        opacity: 0.45, priority: 40 },
  WATER_STRESS:   { label: 'Su Stresi',           color: '#3b82f6', icon: 'droplet',     pattern: 'dot-drop',          opacity: 0.45, priority: 50 },
  THERMAL_STRESS: { label: 'Termal Stres / Sulama', color: '#dc2626', icon: 'thermometer', pattern: 'heatmap-gradient', opacity: 0.55, priority: 55 },
  WEED:           { label: 'Yabanci Ot',          color: '#eab308', icon: 'weed',        pattern: 'dotted',            opacity: 0.60, priority: 60 },
  DISEASE:        { label: 'Hastalik',            color: '#f97316', icon: 'stethoscope', pattern: 'crossline',         opacity: 0.65, priority: 70 },
  FUNGUS:         { label: 'Mantar',              color: '#a855f7', icon: 'mushroom',    pattern: 'cross-hatch',       opacity: 0.65, priority: 75 },
  PEST:           { label: 'Zararli',             color: '#ef4444', icon: 'bug',         pattern: 'x-pattern',         opacity: 0.70, priority: 80 },
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
                opacity: config?.opacity ?? 0.5,
                display: 'inline-block',
              }}
              title={config?.pattern ? `Desen: ${config.pattern}` : undefined}
            />
            <span>{config?.label ?? layer.layerType}</span>
            {config?.icon ? <span aria-hidden="true" className="text-xs text-slate-500 ml-1">[{config.icon}]</span> : null}
          </li>
        );
      })}
    </ul>
  );
}
