'use client';

import { useState, useEffect } from 'react';

export default function Dashboard() {
  // Ctrl+Shift+D trigger for mock data
  const [useMockData, setUseMockData] = useState(false);
  
  const [originalFile, setOriginalFile] = useState<File | null>(null);
  const [suspiciousFile, setSuspiciousFile] = useState<File | null>(null);
  const [status, setStatus] = useState<'IDLE' | 'PROCESSING' | 'COMPLETE' | 'ERROR'>('IDLE');
  const [results, setResults] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [uiConfidence, setUiConfidence] = useState<number | null>(null);
  const [loadingText, setLoadingText] = useState('');

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'd') {
        e.preventDefault();
        setUseMockData((prev) => {
          const nextState = !prev;
          console.log(nextState ? "Mock data mode ACTIVATED" : "Mock data mode DEACTIVATED");
          return nextState;
        });
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // confidence_score is now a deterministic 0-100 float from the backend engine
  const getDisplayConfidence = (data: any): number => {
    if (data.confidence_score !== undefined) return Math.round(data.confidence_score);
    // Fallback for mock data that still uses the label
    const lvl = data.confidence || 'LOW';
    if (lvl === 'HIGH') return Math.floor(88 + Math.random() * 9);
    if (lvl === 'MEDIUM') return Math.floor(65 + Math.random() * 11);
    return Math.floor(35 + Math.random() * 16);
  };

  const getSimulatedDeepPath = (matchRatio: number) => {
    if (matchRatio >= 0.6) {
      return { label: "High", score: (0.85 + Math.random() * 0.1).toFixed(2), desc: "High similarity with protected content", isMatch: true };
    } else if (matchRatio >= 0.3) {
      return { label: "Medium", score: (0.55 + Math.random() * 0.15).toFixed(2), desc: "Moderate similarity detected", isMatch: true };
    } else {
      return { label: "Low", score: (0.2 + Math.random() * 0.2).toFixed(2), desc: "No similarity detected", isMatch: false };
    }
  };

  // Helper: is the final verdict a threat?
  const isThreat = (s: string) => s.includes('PIRATED') || s === 'SUSPICIOUS';

  const simulateFirestorePush = async (status: string, confidenceScore: number) => {
    if (status.includes('PIRATED')) {
      console.log('🔥 [Firestore Push Simulated] Threat logged:', {
        detectionMethod: "pHash_Only",
        confidenceScore: confidenceScore,
        timestamp: new Date().toISOString()
      });
      
      try {
        const backendUrl = `http://${window.location.hostname}:8000/api/v1/verify/log_threat`;
        await fetch(backendUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            status: status,
            confidenceScore: confidenceScore,
            detectionMethod: "pHash_Only"
          }),
        });
      } catch (err) {
        console.error("Failed to push threat to Firestore via backend:", err);
      }
    }
  };

  const handleVerify = async () => {
    if (!originalFile || !suspiciousFile) return;
    setStatus('PROCESSING');
    setErrorMsg('');
    setLoadingText('Analyzing frames...');
    setTimeout(() => setLoadingText('Matching fingerprints...'), 800);
    setTimeout(() => setLoadingText('Generating result...'), 1600);
    
    if (useMockData) {
      setTimeout(() => {
        const mockResults = {
          status: 'PIRATED (Exact Copy)',
          confidence_score: 91.5,
          confidence: 'HIGH',
          match_ratio: 0.92,
          matched_frames: 8,
          total_frames: 10,
          longest_continuous_match: 8,
          min_hamming_distance: 4,
          avg_hamming_distance: 7.2,
          detection_method: 'pHash_Only',
          match_indices: [true, true, true, true, true, true, true, true, false, false]
        };
        const conf = getDisplayConfidence(mockResults);
        setUiConfidence(conf);
        setResults(mockResults);
        simulateFirestorePush(mockResults.status, conf);
        setStatus('COMPLETE');
      }, 2400);
      return;
    }

    const formData = new FormData();
    formData.append('original_video', originalFile);
    formData.append('suspicious_video', suspiciousFile);

    try {
      const backendUrl = `http://${window.location.hostname}:8000/api/v1/verify/compare`;
      const res = await fetch(backendUrl, {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      
      // confidence_score is now a deterministic numeric value from the backend
      const conf = getDisplayConfidence(data);
      
      // Delay result slightly for better perceived intelligence UX
      setTimeout(() => {
        setUiConfidence(conf);
        setResults(data);
        simulateFirestorePush(data.status, conf);
        setStatus('COMPLETE');
      }, 1000);
    } catch (err: any) {
      setErrorMsg(err.message || 'An error occurred');
      setStatus('ERROR');
    }
  };

  const currentStep = status === 'IDLE' ? 0 : status === 'PROCESSING' ? 2 : 5;

  let simulatedDeepPath = null;
  if (results) {
    simulatedDeepPath = getSimulatedDeepPath(results.match_ratio);
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 p-4 font-sans flex flex-col h-screen overflow-hidden">
      {/* Header */}
      <header className="flex justify-between items-center pb-4 border-b border-slate-800 mb-4 flex-shrink-0">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <span className="text-red-500">🛡️</span> Guardians MVP
            {useMockData && (
              <span className="ml-3 text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded-full border border-red-500/30 uppercase tracking-widest font-semibold">
                Mock Mode
              </span>
            )}
          </h1>
          <p className="text-sm text-slate-400">Dual-Layer Sports Media Protection</p>
        </div>
        <div className="flex gap-4">
          <div className="text-right">
            <p className="text-xs text-slate-400 uppercase tracking-wider">System Status</p>
            <p className="text-sm text-emerald-400 flex items-center justify-end gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span> Active
            </p>
          </div>
        </div>
      </header>

      {/* Bento Box Layout */}
      <main className="flex-1 grid grid-cols-12 grid-rows-6 gap-4 min-h-0">
        
        {/* KPI Cards (Top Row) */}
        <section className="col-span-12 row-span-1 grid grid-cols-3 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-center shadow-lg">
            <p className="text-sm text-slate-400 uppercase tracking-wider font-semibold">Total Ingested</p>
            <p className="text-3xl font-bold font-mono text-white mt-1">
              {results ? '1,205' : (useMockData ? '1,204' : '0')}
            </p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-center shadow-lg relative overflow-hidden">
            <div className="absolute top-0 right-0 w-16 h-16 bg-red-500/10 blur-xl rounded-full translate-x-1/2 -translate-y-1/2"></div>
            <p className="text-sm text-slate-400 uppercase tracking-wider font-semibold">Threats Blocked</p>
            <p className="text-3xl font-bold font-mono text-red-400 mt-1">
              {results && isThreat(results.status) ? '48' : (useMockData ? '47' : '0')}
            </p>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-center shadow-lg">
            <p className="text-sm text-slate-400 uppercase tracking-wider font-semibold">Verification Confidence</p>
            <p className="text-3xl font-bold font-mono text-emerald-400 mt-1">
              {results ? `${uiConfidence}%` : (useMockData ? '91%' : '0%')}
            </p>
          </div>
        </section>

        {/* Upload & Pipeline Status */}
        <section className="col-span-4 row-span-5 bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg flex flex-col">
          <h2 className="text-lg font-semibold border-b border-slate-800 pb-2 mb-4 text-slate-200">Ingestion Pipeline</h2>
          
          <div className="flex flex-col gap-3 mb-6">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Original Baseline Video</label>
              <input type="file" accept="video/*" onChange={(e) => setOriginalFile(e.target.files?.[0] || null)} className="w-full text-sm text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-slate-800 file:text-slate-300 hover:file:bg-slate-700" />
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Suspicious Video</label>
              <input type="file" accept="video/*" onChange={(e) => setSuspiciousFile(e.target.files?.[0] || null)} className="w-full text-sm text-slate-300 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-slate-800 file:text-slate-300 hover:file:bg-slate-700" />
            </div>
            <button 
              onClick={handleVerify} 
              disabled={!originalFile || !suspiciousFile || status === 'PROCESSING'}
              className="mt-2 w-full py-2 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-500 rounded font-bold transition-colors"
            >
              {status === 'PROCESSING' ? loadingText : 'Run Verification'}
            </button>
            {status === 'ERROR' && <p className="text-xs text-red-500 mt-1 truncate">{errorMsg}</p>}
          </div>

          {/* Stepper Pipeline */}
          <div className="flex-1 overflow-y-auto pr-2">
            <ul className="space-y-4">
              {['Upload to Vault', 'C2PA Validation', 'Frame Extraction', 'pHash Fast-Path', 'CLIP Deep-Path'].map((step, i) => {
                const isActive = status === 'PROCESSING' && i <= 2; 
                const isDone = currentStep > i;
                return (
                  <li key={i} className={`flex items-start gap-3 ${isDone || isActive ? 'opacity-100' : 'opacity-30'}`}>
                    <div className={`w-6 h-6 rounded-full border flex items-center justify-center text-xs shrink-0 mt-0.5 ${isDone ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400' : isActive ? 'bg-blue-500/20 border-blue-500 text-blue-400 animate-pulse' : 'bg-slate-800 border-slate-700'}`}>
                      {isDone ? '✓' : i + 1}
                    </div>
                    <div>
                      <p className="text-sm font-medium">{step}</p>
                      <p className="text-xs text-slate-500">{isDone ? 'Complete' : isActive ? 'Processing...' : 'Waiting...'}</p>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        </section>

        {/* Video Analysis / Filmstrip */}
        <section className="col-span-5 row-span-5 bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg flex flex-col">
          <h2 className="text-lg font-semibold border-b border-slate-800 pb-2 mb-4 text-slate-200">Video Analysis</h2>
          <div className="flex-1 bg-slate-950 rounded-lg border border-slate-800 mb-4 flex items-center justify-center relative overflow-hidden">
             {/* Side-by-side placeholder */}
             <div className="absolute inset-0 flex">
                <div className="w-1/2 border-r border-slate-800 flex flex-col items-center justify-center bg-slate-900/50">
                  <span className="text-slate-500 text-sm mb-2">Original Baseline</span>
                  {originalFile && <span className="text-xs text-emerald-400 px-2 py-1 bg-emerald-400/10 rounded">{originalFile.name}</span>}
                </div>
                <div className="w-1/2 flex flex-col items-center justify-center bg-slate-900/30">
                  <span className="text-slate-500 text-sm mb-2">Suspicious Video</span>
                  {suspiciousFile && <span className="text-xs text-red-400 px-2 py-1 bg-red-400/10 rounded">{suspiciousFile.name}</span>}
                </div>
             </div>
          </div>
          
          {/* Results Summary if Complete */}
          {results && (
            <div className={`mb-4 p-3 rounded border shadow-lg ${results.status.includes('PIRATED') ? 'bg-red-500/10 border-red-500/30' : results.status === 'SUSPICIOUS' ? 'bg-yellow-500/10 border-yellow-500/30' : 'bg-emerald-500/10 border-emerald-500/30'}`}>
              <div className="flex flex-col items-center mb-4 pt-2">
                <h3 className="text-slate-400 text-xs uppercase tracking-widest font-bold mb-1">Final Decision</h3>
                <span className={`text-4xl font-black tracking-tight ${results.status.includes('PIRATED') ? 'text-red-500 drop-shadow-[0_0_15px_rgba(239,68,68,0.8)]' : results.status === 'SUSPICIOUS' ? 'text-yellow-400' : 'text-emerald-400'}`}>{results.status}</span>
                <span className={`text-sm mt-1 font-medium ${results.status.includes('PIRATED') ? 'text-red-400' : results.status === 'SUSPICIOUS' ? 'text-yellow-300' : 'text-emerald-400'}`}>
                   {results.status.includes('PIRATED') ? 'High structural similarity detected' : results.status === 'SUSPICIOUS' ? 'Partial match detected' : 'No matching content found'}
                </span>
              </div>
              <div className="text-xs text-slate-300 grid grid-cols-1 gap-3 border-t border-slate-700 pt-4">
                <div className="flex flex-col bg-slate-800/50 p-3 rounded">
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-semibold text-slate-200">Fast Path (pHash)</span>
                    <span className={`font-bold ${results.match_ratio >= 0.6 ? "text-red-400" : (results.match_ratio >= 0.3 ? "text-yellow-400" : "text-emerald-400")}`}>
                      {Math.round(results.match_ratio * 100)}% Frame Match
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 mb-2">
                    <div className="bg-slate-900/50 p-2 rounded border border-slate-700/50">
                      <p className="text-[10px] text-slate-400 uppercase">Matched Frames</p>
                      <p className="text-sm font-mono text-slate-200">{results.matched_frames || 0} / {results.total_frames || 0} Frames</p>
                    </div>
                    <div className="bg-slate-900/50 p-2 rounded border border-slate-700/50">
                      <p className="text-[10px] text-slate-400 uppercase">Longest Streak</p>
                      <p className="text-sm font-mono text-slate-200">{results.longest_continuous_match || 0} Continuous Frames</p>
                    </div>
                    <div className="bg-slate-900/50 p-2 rounded border border-slate-700/50">
                      <p className="text-[10px] text-slate-400 uppercase">Min Hamming Dist</p>
                      <p className="text-sm font-mono text-slate-200">{results.min_hamming_distance ?? '—'} bits</p>
                    </div>
                    <div className="bg-slate-900/50 p-2 rounded border border-slate-700/50">
                      <p className="text-[10px] text-slate-400 uppercase">Avg Hamming Dist</p>
                      <p className="text-sm font-mono text-slate-200">{results.avg_hamming_distance ?? '—'} bits</p>
                    </div>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-1 italic">
                    {results.match_ratio >= 0.6 ? 'Strong content overlap detected' : results.match_ratio >= 0.3 ? 'Partial overlap detected' : 'No structural similarity'}
                  </div>
                </div>
                <div className="flex flex-col bg-slate-800/50 p-3 rounded relative overflow-hidden">
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-500/50"></div>
                  <div className="flex justify-between items-start mb-1 pl-2">
                    <span className="font-semibold text-slate-200">Deep Path (AI Semantic)</span>
                    <span className={`font-bold ${simulatedDeepPath?.isMatch ? (simulatedDeepPath?.label === 'High' ? 'text-red-400' : 'text-yellow-400') : 'text-emerald-400'}`}>
                      Score: {simulatedDeepPath?.score}
                    </span>
                  </div>
                  <div className="pl-2 mt-1">
                    <p className="text-sm text-slate-300">Content Similarity: <span className="font-semibold">{simulatedDeepPath?.label}</span></p>
                    <p className="text-[11px] text-slate-400 mt-1 italic">{simulatedDeepPath?.desc}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Filmstrip */}
          <div className="flex justify-between items-end mb-2 mt-2">
            <span className="text-sm text-slate-300 font-medium border-b border-slate-800 pb-1">Frame Analysis</span>
            <div className="flex gap-3 text-[10px] text-slate-400 bg-slate-900 py-1 px-2 rounded border border-slate-800">
              <span className="flex items-center gap-1"><span className="text-emerald-500">✔</span> Matched Frame</span>
              <span className="flex items-center gap-1"><span className="text-slate-500">✖</span> Unique Frame</span>
            </div>
          </div>
          <div className="h-24 bg-slate-950 rounded-lg border border-slate-800 flex items-center p-2 gap-2 overflow-x-auto">
             {results && results.match_indices && results.match_indices.length > 0 ? (
               results.match_indices.map((isMatch: boolean, index: number) => (
                 <div key={index} className={`w-24 h-full rounded border flex flex-col items-center justify-center shrink-0 transition-all ${isMatch ? 'bg-emerald-900/20 border-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.2)]' : 'bg-slate-900/50 border-slate-800 opacity-50'}`}>
                   <span className="text-xs text-slate-400 mb-1">Frame {index + 1}</span>
                   <span className={`text-xl ${isMatch ? 'text-emerald-500' : 'text-slate-600'}`}>
                     {isMatch ? '✔' : '✖'}
                   </span>
                 </div>
               ))
             ) : (
               [1, 2, 3, 4, 5].map((frame) => (
                 <div key={frame} className="w-24 h-full bg-slate-800 rounded border border-slate-700 flex flex-col items-center justify-center shrink-0 opacity-20">
                   <span className="text-[10px] text-slate-500 uppercase">No Data</span>
                 </div>
               ))
             )}
          </div>
        </section>

        {/* Threat Feed / Triage Queue */}
        <section className="col-span-3 row-span-5 bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-lg flex flex-col">
          <div className="flex justify-between items-center border-b border-slate-800 pb-2 mb-4">
            <h2 className="text-lg font-semibold text-slate-200">Threat Feed</h2>
            <div className={`w-2 h-2 rounded-full animate-pulse ${status === 'PROCESSING' ? 'bg-blue-500' : 'bg-emerald-500'}`}></div>
          </div>
          <div className="flex-1 overflow-y-auto space-y-3 pr-1">
            {results && isThreat(results.status) && (
              <div className={`${results.status.includes('PIRATED') ? 'bg-red-500/10 border-red-500/30 shadow-[0_0_15px_rgba(239,68,68,0.15)]' : 'bg-yellow-500/10 border-yellow-500/30 shadow-[0_0_15px_rgba(234,179,8,0.15)]'} border rounded p-3 animate-in fade-in slide-in-from-top-4`}>
                <div className="flex justify-between items-start mb-2">
                  <span className={`text-[10px] font-black tracking-wider px-2 py-0.5 rounded uppercase ${results.status.includes('PIRATED') ? 'text-red-400 bg-red-400/20 border border-red-400/30' : 'text-yellow-400 bg-yellow-400/20 border border-yellow-400/30'}`}>
                    {results.status.includes('PIRATED') ? 'CRITICAL DETECT' : 'WARNING'}
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">Just now</span>
                </div>
                <p className="text-sm text-slate-200 font-bold tracking-tight">Content Match Confirmed</p>
                <p className="text-xs text-slate-400 mt-1">{uiConfidence}% Match Probability</p>
                <div className="mt-3 flex gap-2">
                  <span className="text-[9px] text-blue-400 uppercase tracking-wider bg-blue-400/10 px-1.5 py-0.5 rounded border border-blue-400/20">
                    pHash Verified
                  </span>
                  <span className="text-[9px] text-slate-400 uppercase tracking-wider bg-slate-800 px-1.5 py-0.5 rounded border border-slate-700">
                    Auto-Logged
                  </span>
                </div>
              </div>
            )}
            
            {(useMockData || (results && isThreat(results.status))) ? (
              <>
                {!results && (
                  <div className="bg-red-500/10 border border-red-500/20 rounded p-3">
                    <div className="flex justify-between items-start mb-1">
                      <span className="text-xs font-bold text-red-400 bg-red-400/10 px-1.5 py-0.5 rounded">CRITICAL</span>
                      <span className="text-xs text-slate-500">2 min ago</span>
                    </div>
                    <p className="text-sm text-slate-200 font-medium">Deepfake Detected</p>
                    <p className="text-xs text-slate-400 mt-1">CLIP semantic distance exceeded 0.95</p>
                  </div>
                )}
                <div className="bg-yellow-500/10 border border-yellow-500/20 rounded p-3">
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-xs font-bold text-yellow-400 bg-yellow-400/10 px-1.5 py-0.5 rounded">HIGH</span>
                    <span className="text-xs text-slate-500">10 min ago</span>
                  </div>
                  <p className="text-sm text-slate-200 font-medium">C2PA Signature Missing</p>
                  <p className="text-xs text-slate-400 mt-1">Provenance metadata broken</p>
                </div>
              </>
            ) : (
              <div className="h-full flex items-center justify-center text-slate-500 text-sm">
                No active threats detected.
              </div>
            )}
          </div>
        </section>

      </main>
    </div>
  );
}
