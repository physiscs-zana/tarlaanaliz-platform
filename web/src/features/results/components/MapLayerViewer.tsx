/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-064 v1.2.0: Harita katman render bileseni. */
/* KR-084 v1.2.0: THERMAL_STRESS katmani — Dark Red/Orange gradient + termometre ikonu. */

'use client';

import type { ResultLayer } from '../services/resultService';
import type { ThermalSummary } from '../services/resultService';

/** KR-084: Termal stres gosterge paneli. */
interface ThermalOverlayProps {
  readonly thermalSummary: ThermalSummary;
}

function ThermalOverlay({ thermalSummary }: ThermalOverlayProps) {
  return (
    <div
      style={{
        padding: 12,
        /* KR-084: 3-stop gradient — Koyu Kırmızı (yüksek stres) → Turuncu (orta) → Açık Sarı (düşük) */
        background: 'linear-gradient(135deg, #dc2626, #f97316, #fde047)',
        borderRadius: 8,
        color: '#fff',
        fontSize: 14,
      }}
    >
      <strong>Termal Stres / Sulama Analizi (KR-084)</strong>
      <ul style={{ listStyle: 'none', padding: 0, marginTop: 8 }}>
        <li>CWSI: {thermalSummary.cwsi.toFixed(2)}</li>
        <li>Kanopi Sicakligi: {thermalSummary.canopyTemp.toFixed(1)} C</li>
        <li>Kanopi-Toprak deltaT: {thermalSummary.canopySoilDeltaT.toFixed(1)} C</li>
        <li>Sulama Verimliligi: {(thermalSummary.irrigationEfficiency * 100).toFixed(0)}%</li>
      </ul>
    </div>
  );
}

interface MapLayerViewerProps {
  readonly layers: readonly ResultLayer[];
  readonly visibleLayers?: ReadonlySet<string>;
  readonly thermalSummary?: ThermalSummary | null;
}

/**
 * Harita katman render bileseni.
 *
 * Gercek harita entegrasyonu (Leaflet/Mapbox) ileride eklenecek.
 * Bu bilesen katman listesini ve termal ozet panelini gosterir.
 */
export function MapLayerViewer({ layers, visibleLayers, thermalSummary }: MapLayerViewerProps) {
  const visible = layers.filter((l) => !visibleLayers || visibleLayers.has(l.layerName));

  const hasThermalLayer = visible.some((l) => l.layerType === 'THERMAL_STRESS');

  return (
    <div>
      <div aria-label="Harita katmanlari gorunumu">
        {visible.map((layer) => (
          <div key={layer.layerName} style={{ padding: '4px 0', fontSize: 13 }}>
            [{layer.layerType}] {layer.layerName} — {layer.uri}
          </div>
        ))}
        {visible.length === 0 && <p>Gorunur katman yok.</p>}
      </div>

      {hasThermalLayer && thermalSummary && (
        <ThermalOverlay thermalSummary={thermalSummary} />
      )}
    </div>
  );
}
