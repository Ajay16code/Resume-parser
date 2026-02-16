import { useState } from 'react'

const API_BASE_URL = import.meta.env.VITE_API_URL || `${window.location.protocol}//${window.location.hostname}:8000`

export default function App() {
  const [resume, setResume] = useState(null)
  const [textMode, setTextMode] = useState(false)
  const [resumeText, setResumeText] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [downloadLoading, setDownloadLoading] = useState(false)
  const [page, setPage] = useState('analyze') // 'analyze' | 'dashboard'
  const [dashboard, setDashboard] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('resume_dashboard') || '[]')
    } catch (_) {
      return []
    }
  })

  const onSubmit = async (event) => {
    event.preventDefault()
    if (!textMode && !resume) {
      setError('Please upload a PDF or enable Text mode and provide resume text.')
      return
    }
    if (textMode && !resumeText.trim()) {
      setError('Please paste resume text when Text mode is enabled.')
      return
    }
    if (!jobDescription.trim()) {
      setError('Please provide a job description.')
      return
    }

    setLoading(true)
    setError('')
    setResult(null)

    try {
      let endpoint = `${API_BASE_URL}/analyze`
      let body = null
      let headers = undefined

      if (textMode) {
        endpoint = `${API_BASE_URL}/analyze_text`
        body = JSON.stringify({ resume_text: resumeText, job_description: jobDescription })
        headers = { 'Content-Type': 'application/json' }
      } else {
        const formData = new FormData()
        formData.append('resume', resume)
        formData.append('job_description', jobDescription)
        body = formData
      }

      const response = await fetch(endpoint, { method: 'POST', body, headers })
      if (!response.ok) {
        const text = await response.text().catch(() => '')
        throw new Error(`Analysis failed (${response.status}): ${text || response.statusText}`)
      }
      const payload = await response.json()
      setResult(payload)
    } catch (err) {
      console.error(err)
      setError(err.message || String(err))
    } finally {
      setLoading(false)
    }
  }

  const parseResume = async () => {
    if (!resume) {
      setError('Please upload a PDF to parse.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('resume', resume)
      if (jobDescription && jobDescription.trim()) {
        formData.append('job_description', jobDescription)
      }

      const res = await fetch(`${API_BASE_URL}/parse_resume`, { method: 'POST', body: formData })
      if (!res.ok) throw new Error(`Parse failed: ${res.status}`)
      const parsed = await res.json()
      setResult((r) => ({ ...(r || {}), parsed }))
    } catch (e) {
      setError(e.message || String(e))
    } finally {
      setLoading(false)
    }
  }

  const saveToDashboard = () => {
    if (!result || !result.parsed) {
      setError('No parsed resume to save. Run Parse first.')
      return
    }
    const entry = {
      id: Date.now(),
      file: resume?.name || result.parsed.name || `resume-${Date.now()}`,
      parsed: result.parsed,
      analyzed: result,
      saved_at: new Date().toISOString(),
    }
    const next = [entry, ...dashboard]
    setDashboard(next)
    localStorage.setItem('resume_dashboard', JSON.stringify(next))
    setPage('dashboard')
  }

  const removeDashboardEntry = (id) => {
    const next = dashboard.filter((d) => d.id !== id)
    setDashboard(next)
    localStorage.setItem('resume_dashboard', JSON.stringify(next))
  }

  const downloadDatasetReport = async () => {
    try {
      setDownloadLoading(true)
      const response = await fetch(`${API_BASE_URL}/download_dataset_report`)
      if (!response.ok) {
        throw new Error(`Failed to download report: ${response.status}`)
      }
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'dataset_analysis_report.pdf')
      document.body.appendChild(link)
      link.click()
      link.parentNode.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError(err.message || 'Failed to download report')
    } finally {
      setDownloadLoading(false)
    }
  }

  return (
    <main className="min-h-screen p-4 md:p-8 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <section className="mx-auto max-w-5xl rounded-2xl bg-white/95 backdrop-blur p-8 md:p-12 shadow-2xl border border-white/20">
        {/* Header Section */}
        <div className="mb-8 border-b border-gradient-to-r from-blue-500 to-purple-500 pb-8">
          <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-blue-600 bg-clip-text text-transparent">
               Resume Intelligence Engine
          </h1>
          <p className="mt-3 text-lg text-slate-600">Analyze candidate resumes with AI-powered matching against job descriptions</p>
        </div>

        {/* Navigation Tabs */}
        <div className="mb-8 flex flex-wrap gap-3 items-center justify-between">
          <div className="flex gap-3">
            <button 
              onClick={() => setPage('analyze')} 
              className={`px-6 py-2.5 rounded-lg font-semibold transition-all duration-300 ${
                page==='analyze' 
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/30' 
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
               Analyze
            </button>
            <button 
              onClick={() => setPage('dashboard')} 
              className={`px-6 py-2.5 rounded-lg font-semibold transition-all duration-300 ${
                page==='dashboard' 
                  ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg shadow-blue-500/30' 
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
               Dashboard
            </button>
          </div>
          <button 
            onClick={downloadDatasetReport} 
            disabled={downloadLoading}
            className="ml-auto px-6 py-2.5 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-semibold hover:shadow-lg hover:shadow-emerald-500/30 disabled:opacity-50 transition-all duration-300 flex items-center gap-2"
          >
            {downloadLoading ? '⏳ Generating...' : ' Export Report (PDF)'} 
          </button>
        </div>

        {page === 'analyze' && (
          <form className="mt-8 space-y-6" onSubmit={onSubmit}>
            {/* Resume Upload Section */}
            <div className="rounded-xl bg-gradient-to-br from-blue-50 to-purple-50 p-6 border border-blue-200">
              <label className="mb-3 block text-sm font-bold text-slate-800">  Upload Resume (PDF)</label>
              <input
                type="file"
                accept="application/pdf"
                onChange={(e) => setResume(e.target.files?.[0] ?? null)}
                className="w-full rounded-lg border-2 border-dashed border-blue-400 p-4 bg-white transition-all hover:border-blue-500 focus:outline-none"
                disabled={textMode}
              />
              {resume && <p className="mt-2 text-sm text-green-600 font-medium">✓ {resume.name} selected</p>}
            </div>

            {/* Text Mode Toggle */}
            <div className="flex items-center gap-3 rounded-lg bg-slate-50 p-4 border border-slate-200">
              <input 
                type="checkbox" 
                id="textMode"
                checked={textMode} 
                onChange={(e) => setTextMode(e.target.checked)}
                className="w-5 h-5 accent-blue-600"
              />
              <label htmlFor="textMode" className="text-sm font-semibold text-slate-700 cursor-pointer">
                  Or paste resume text instead
              </label>
            </div>

            {/* Resume Text Textarea */}
            {textMode && (
              <div className="rounded-xl bg-gradient-to-br from-purple-50 to-pink-50 p-6 border border-purple-200">
                <label className="mb-3 block text-sm font-bold text-slate-800">📋 Resume Text</label>
                <textarea
                  rows={8}
                  value={resumeText}
                  onChange={(e) => setResumeText(e.target.value)}
                  className="w-full rounded-lg border-2 border-purple-300 p-4 bg-white font-mono text-sm focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-200"
                  placeholder="Paste your resume text here..."
                />
              </div>
            )}

            {/* Job Description Textarea */}
            <div className="rounded-xl bg-gradient-to-br from-emerald-50 to-cyan-50 p-6 border border-emerald-200">
              <label className="mb-3 block text-sm font-bold text-slate-800">  Job Description</label>
              <textarea
                rows={7}
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                className="w-full rounded-lg border-2 border-emerald-300 p-4 bg-white font-mono text-sm focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-200"
                placeholder="Paste the job description here..."
              />
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-3">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 md:flex-none rounded-lg bg-gradient-to-r from-blue-600 to-blue-700 px-6 py-3 font-bold text-white hover:shadow-lg hover:shadow-blue-500/30 disabled:opacity-50 transition-all duration-300"
              >
                {loading ? '⏳ Analyzing...' : ' Analyze Candidate'}
              </button>

              <button 
                type="button" 
                onClick={parseResume} 
                className="flex-1 md:flex-none rounded-lg bg-gradient-to-r from-emerald-600 to-emerald-700 px-6 py-3 font-bold text-white hover:shadow-lg hover:shadow-emerald-500/30 transition-all duration-300"
              >
                 Parse Resume
              </button>
              
              <button 
                type="button" 
                onClick={saveToDashboard} 
                className="flex-1 md:flex-none rounded-lg bg-gradient-to-r from-slate-600 to-slate-700 px-6 py-3 font-bold text-white hover:shadow-lg hover:shadow-slate-500/30 transition-all duration-300"
              >
                 Save to Dashboard
              </button>
            </div>
          </form>
        )}

        {page === 'dashboard' && (
          <div className="mt-8">
            <h2 className="text-3xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">  Saved Resumes</h2>
            {dashboard.length === 0 ? (
              <div className="rounded-xl bg-gradient-to-br from-slate-100 to-slate-50 p-12 text-center border border-slate-200">
                <p className="text-lg text-slate-600">  No saved resumes yet</p>
                <p className="text-sm text-slate-500 mt-2">Parse and save resumes from the Analyze tab to see them here</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {dashboard.map((entry) => (
                  <div key={entry.id} className="rounded-xl bg-gradient-to-br from-white to-slate-50 border border-slate-200 p-6 hover:shadow-lg transition-all duration-300">
                    <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
                      <div className="flex-1">
                        <div className="font-bold text-lg text-slate-800">  {entry.file}</div>
                        <div className="text-sm text-slate-500 mt-2">
                           Saved: {new Date(entry.saved_at).toLocaleDateString()} at {new Date(entry.saved_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2 md:gap-3">
                        <button 
                          onClick={() => setResult(entry.analyzed)} 
                          className="rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 text-white px-4 py-2 font-semibold hover:shadow-lg hover:shadow-blue-500/30 transition-all duration-300"
                        >
                           Analysis
                        </button>
                        <button 
                          onClick={() => setResult({ parsed: entry.parsed })} 
                          className="rounded-lg bg-gradient-to-r from-amber-500 to-amber-600 text-white px-4 py-2 font-semibold hover:shadow-lg hover:shadow-amber-500/30 transition-all duration-300"
                        >
                           Parse
                        </button>
                        <button 
                          onClick={() => removeDashboardEntry(entry.id)} 
                          className="rounded-lg bg-gradient-to-r from-red-500 to-red-600 text-white px-4 py-2 font-semibold hover:shadow-lg hover:shadow-red-500/30 transition-all duration-300"
                        >
                          🗑️ Remove
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="mt-8 rounded-xl bg-gradient-to-br from-red-50 to-pink-50 p-6 border-2 border-red-300 shadow-lg">
            <p className="text-red-700 font-semibold flex items-center gap-2">
              ⚠️ {error}
            </p>
          </div>
        )}

        {result && (
          <div className="mt-8 space-y-6 rounded-2xl bg-gradient-to-br from-slate-50 to-slate-100 p-8 border border-slate-200">
            {/* Results Summary Cards */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className={`rounded-xl p-6 shadow-lg transition-all transform hover:scale-105 ${
                result.prediction === 'Fit' 
                  ? 'bg-gradient-to-br from-emerald-400 to-green-500 text-white shadow-emerald-500/30' 
                  : 'bg-gradient-to-br from-red-400 to-pink-500 text-white shadow-red-500/30'
              }`}>
                <p className="text-xs font-bold uppercase tracking-wide opacity-90"> Match Status</p>
                <p className="text-3xl font-bold mt-2">{result.prediction}</p>
              </div>
              
              <div className="rounded-xl bg-gradient-to-br from-blue-400 to-cyan-500 text-white p-6 shadow-lg shadow-blue-500/30 transition-all transform hover:scale-105">
                <p className="text-xs font-bold uppercase tracking-wide opacity-90"> Confidence</p>
                <p className="text-3xl font-bold mt-2">{(result.confidence_score * 100).toFixed(1)}%</p>
              </div>
              
              <div className="rounded-xl bg-gradient-to-br from-purple-400 to-pink-500 text-white p-6 shadow-lg shadow-purple-500/30 transition-all transform hover:scale-105">
                <p className="text-xs font-bold uppercase tracking-wide opacity-90">  Similarity</p>
                <p className="text-3xl font-bold mt-2">{result.similarity_score.toFixed(3)}</p>
              </div>
            </div>
            
            {/* Skills Comparison */}
            {result.resume_skills && result.resume_skills.length > 0 && (
              <div className="rounded-xl bg-white p-6 border border-blue-200 shadow-md">
                <p className="mb-4 font-bold text-lg text-slate-800 flex items-center gap-2">
                  🧠 Detected Resume Skills
                </p>
                <div className="flex flex-wrap gap-2">
                  {result.resume_skills.map((skill, i) => (
                    <span key={i} className="inline-block rounded-full bg-gradient-to-r from-blue-100 to-cyan-100 text-blue-900 px-4 py-2 text-sm font-semibold hover:shadow-lg transition-all duration-300">
                      {skill} ✓
                    </span>
                  ))}
                </div>
              </div>
            )}

            {result.job_skills && result.job_skills.length > 0 && (
              <div className="rounded-xl bg-white p-6 border border-amber-200 shadow-md">
                <p className="mb-4 font-bold text-lg text-slate-800 flex items-center gap-2">
                    Required Job Skills
                </p>
                <div className="flex flex-wrap gap-2">
                  {result.job_skills.map((skill, i) => (
                    <span key={i} className="inline-block rounded-full bg-gradient-to-r from-amber-100 to-yellow-100 text-amber-900 px-4 py-2 text-sm font-semibold hover:shadow-lg transition-all duration-300">
                      {skill} ⭐
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Parsed Data */}
            {result.parsed && (
              <div className="rounded-xl bg-white p-6 border border-slate-300 shadow-md">
                <p className="mb-4 font-bold text-lg text-slate-800">📋 Parsed Resume Data</p>
                <div className="space-y-3 text-sm text-slate-700">
                  {Object.entries(result.parsed).slice(0, 5).map(([key, value]) => (
                    <div key={key} className="flex justify-between items-center pb-2 border-b border-slate-200 last:border-b-0">
                      <span className="font-semibold text-slate-600">{key}:</span>
                      <span className="text-right">{JSON.stringify(value).substring(0, 40)}...</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </section>
    </main>
  )
}
