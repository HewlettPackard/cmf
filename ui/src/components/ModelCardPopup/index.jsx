/***
 * Copyright (2023) Hewlett Packard Enterprise Development LP
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * You may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ***/

const SECTION_META = [
  { title: "Model Data", icon: "M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v3.57A22.952 22.952 0 0110 13a22.95 22.95 0 01-8-1.43V8a2 2 0 012-2h2zm2-1a1 1 0 011-1h2a1 1 0 011 1v1H8V5zm1 5a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z M2 13.692V16a2 2 0 002 2h12a2 2 0 002-2v-2.308A24.974 24.974 0 0110 15c-2.796 0-5.487-.46-8-1.308z", color: "teal" },
  { title: "Executions Using This Model", icon: "M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z", color: "blue" },
  { title: "Input Artifacts", icon: "M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z", color: "green" },
  { title: "Output Artifacts", icon: "M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 9.293a1 1 0 000 1.414L9 13.414V5a1 1 0 112 0v8.414l2.707-2.707a1 1 0 011.414 1.414l-3.999 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z", color: "purple" },
];

const ModelCardPopup = ({ show, model_data, onClose }) => {
  if (!show) return null;

  const findUri = () => {
    const item = model_data[0].find((entry) => entry.uri);
    return item ? item.uri : "default";
  };

  const downloadJSON = () => {
    const uri = findUri();
    const filename = `model_card_${uri}.json`;
    const blob = new Blob([JSON.stringify(model_data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const excludeColumns = ["create_time_since_epoch"];

  const renameKey = (key) => {
    const prefix = "custom_properties_";
    return key.startsWith(prefix) ? key.slice(prefix.length) : key;
  };

  /* ── Key-value card list (cases 0, 2, 3) ── */
  const renderKVList = (item, sectionIndex) => {
    const accentColor = sectionIndex === 2 ? "border-l-green-500" : sectionIndex === 3 ? "border-l-purple-500" : "border-l-teal-500";
    return item.length > 0 ? (
      <div className="space-y-4">
        {item.map((data, i) => {
          const entries = Object.entries(data).filter(([key]) => !excludeColumns.includes(key));
          return (
            <div key={i} className={`rounded-lg border-2 border-gray-300 border-l-4 ${accentColor} overflow-hidden shadow-sm`}>
              {entries.map(([key, value], idx) => (
                <div
                  key={idx}
                  className={`flex items-start gap-3 px-4 py-2.5 ${idx % 2 === 0 ? "bg-gray-50" : "bg-white"} ${idx > 0 ? "border-t border-gray-200" : ""}`}
                >
                  <span className="w-1/3 text-xs font-bold text-gray-500 uppercase tracking-wide pt-0.5 break-all">
                    {renameKey(key)}
                  </span>
                  <span className="w-2/3 text-sm text-gray-900 break-all">
                    {value !== null && value !== undefined && value !== "" ? String(value) : <span className="text-gray-400 italic">—</span>}
                  </span>
                </div>
              ))}
            </div>
          );
        })}
      </div>
    ) : (
      <p className="text-sm text-gray-400 italic">No data available</p>
    );
  };

  /* ── Execution table (case 1) ── */
  const renderTable = (item) => {
    const headers = item.length > 0 ? Object.keys(item[0]) : [];
    return item.length > 0 ? (
      <div className="max-h-64 overflow-y-auto overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-sm border-collapse min-w-max">
          <thead className="sticky top-0 z-10">
            <tr className="bg-teal-600 text-white">
              {headers.map((header, idx) => (
                <th key={idx} className="px-4 py-2.5 text-left font-semibold whitespace-nowrap">
                  {renameKey(header)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {item.map((data, i) => (
              <tr key={i} className={`${i % 2 === 0 ? "bg-white" : "bg-gray-50"} hover:bg-teal-50 transition-colors`}>
                {headers.map((header, idx) => (
                  <td key={idx} className="px-4 py-2.5 border-t border-gray-100 text-gray-800 break-all">
                    {data[header] !== null && data[header] !== undefined ? String(data[header]) : <span className="text-gray-400 italic">—</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    ) : (
      <p className="text-sm text-gray-400 italic">No executions found</p>
    );
  };

  const renderContent = (item, index) => {
    if (index === 1) return renderTable(item);
    return renderKVList(item, index);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col overflow-hidden">

        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-teal-50 to-white rounded-t-xl flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="bg-teal-100 rounded-lg p-2">
              <svg className="w-5 h-5 text-teal-700" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v3.57A22.952 22.952 0 0110 13a22.95 22.95 0 01-8-1.43V8a2 2 0 012-2h2zm2-1a1 1 0 011-1h2a1 1 0 011 1v1H8V5zm1 5a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z" clipRule="evenodd" />
                <path d="M2 13.692V16a2 2 0 002 2h12a2 2 0 002-2v-2.308A24.974 24.974 0 0110 15c-2.796 0-5.487-.46-8-1.308z" />
              </svg>
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">Model Card</h2>
              <p className="text-xs text-gray-500">Metadata associated with the model</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={downloadJSON}
              className="flex items-center gap-1.5 px-3 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 hover:border-teal-400 transition-all shadow-sm"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Download
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">
          {model_data.length > 0 ? (
            model_data.map((item, index) => {
              const meta = SECTION_META[index] || { title: `Section ${index + 1}`, color: "gray" };
              return (
                <div key={index} className="rounded-xl border border-gray-200 overflow-hidden shadow-sm">
                  {/* Section header */}
                  <div className={`flex items-center gap-2 px-4 py-3 bg-${meta.color}-50 border-b border-${meta.color}-100`}>
                    <svg className={`w-4 h-4 text-${meta.color}-600`} fill="currentColor" viewBox="0 0 20 20">
                      <path d={meta.icon} />
                    </svg>
                    <h3 className={`text-sm font-bold text-${meta.color}-700 uppercase tracking-wide`}>
                      {meta.title}
                    </h3>
                  </div>
                  {/* Section content */}
                  <div className="p-4">
                    {renderContent(item, index)}
                  </div>
                </div>
              );
            })
          ) : (
            <p className="text-gray-400 text-sm text-center py-12">No model data available</p>
          )}
        </div>

      </div>
    </div>
  );
};

export default ModelCardPopup;
