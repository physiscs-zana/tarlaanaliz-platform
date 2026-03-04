/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-081: Field listesi contract-first tipli render edilir. */

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Farmer Fields",
};

interface FieldItem {
  readonly id: string;
  readonly name: string;
  readonly areaDecare: number;
}

const fields: readonly FieldItem[] = [{ id: "fld_001", name: "Kuzey Parsel", areaDecare: 24.5 }];

function FieldMapStub() {
  return <div className="h-56 rounded bg-slate-100 p-3 text-sm text-slate-600">FieldMap entegrasyon noktası (stub)</div>;
}

function AddFieldModalStub() {
  return (
    <button type="button" className="rounded border px-3 py-2 text-sm hover:bg-slate-50">
      AddFieldModal entegrasyon noktası (stub)
    </button>
  );
}

export default function FarmerFieldsPage() {
  return (
    <section className="space-y-4" aria-label="Farmer fields" data-corr-id="pending" data-request-id="pending">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Tarlalarım</h1>
        <AddFieldModalStub />
      </div>
      <FieldMapStub />
      <div className="rounded-lg border border-slate-200 bg-white">
        <ul className="divide-y divide-slate-200 text-sm">
          {fields.map((field) => (
            <li key={field.id} className="p-3">
              {field.name} · {field.areaDecare} da
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
