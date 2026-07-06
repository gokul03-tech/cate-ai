/**
 * LexOrch-KG — Landing Page
 * Marketing hero with features, stats, and CTA.
 */

import { Link } from 'react-router-dom'
import {
  Scale, Network, Brain, MessageSquare, Lightbulb,
  FileText, Shield, ChevronRight, Star, Zap, Globe,
  GitBranch, Upload, CheckCircle,
} from 'lucide-react'

const features = [
  {
    icon: Brain,
    color: 'from-blue-500 to-indigo-600',
    title: 'Multi-Agent AI Pipeline',
    desc: '8 specialized AI agents work in concert — from document parsing to final recommendation.',
  },
  {
    icon: Network,
    color: 'from-purple-500 to-pink-600',
    title: 'Knowledge Graph Reasoning',
    desc: 'Neo4j-powered legal knowledge graph connects judges, courts, laws, and precedents.',
  },
  {
    icon: MessageSquare,
    color: 'from-emerald-500 to-teal-600',
    title: 'Adversarial Debate',
    desc: 'Prosecution, Defense, Judge, and Consensus agents debate every case independently.',
  },
  {
    icon: Lightbulb,
    color: 'from-amber-500 to-orange-600',
    title: 'Explainable AI (XAI)',
    desc: 'Every recommendation comes with a transparent reasoning chain and confidence scores.',
  },
  {
    icon: GitBranch,
    color: 'from-cyan-500 to-blue-600',
    title: 'RAG + Semantic Search',
    desc: 'ChromaDB vector store retrieves similar precedents using BAAI/bge-base-en embeddings.',
  },
  {
    icon: FileText,
    color: 'from-rose-500 to-red-600',
    title: 'Professional Reports',
    desc: 'Generate PDF, JSON, and HTML reports with ReportLab for case documentation.',
  },
]

const stats = [
  { label: 'AI Agents', value: '8' },
  { label: 'Graph Relationships', value: '12+' },
  { label: 'Entity Types', value: '13' },
  { label: 'Report Formats', value: '3' },
]

const agentSteps = [
  { step: 1, name: 'Case Understanding',   color: '#3a70f5' },
  { step: 2, name: 'Entity Extraction',    color: '#8b5cf6' },
  { step: 3, name: 'Knowledge Graph',      color: '#10b981' },
  { step: 4, name: 'RAG Retrieval',        color: '#f59e0b' },
  { step: 5, name: 'Legal Reasoning',      color: '#ef4444' },
  { step: 6, name: 'Multi-Agent Debate',   color: '#06b6d4' },
  { step: 7, name: 'Explainability',       color: '#6366f1' },
  { step: 8, name: 'Report Generation',    color: '#84cc16' },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-dark-950 text-dark-100">
      {/* ── Header ──────────────────────────────────────────────── */}
      <header className="border-b border-dark-700/50 backdrop-blur-sm sticky top-0 z-50 bg-dark-950/80">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center">
              <Scale className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold gradient-text text-lg">LexOrch-KG</span>
              <p className="text-[10px] text-dark-500 -mt-0.5">Legal Decision Support</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login" className="btn-secondary text-sm py-2 px-4">Sign In</Link>
            <Link to="/register" className="btn-primary text-sm py-2 px-4">Get Started</Link>
          </div>
        </div>
      </header>

      {/* ── Hero ────────────────────────────────────────────────── */}
      <section className="relative py-24 px-6 text-center overflow-hidden grid-bg">
        {/* Background glow */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-600/10 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent-500/5 rounded-full blur-3xl" />
        </div>

        <div className="relative max-w-5xl mx-auto animate-slide-up">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-500/10 border border-primary-500/20 mb-8">
            <Zap className="w-4 h-4 text-primary-400" />
            <span className="text-sm text-primary-300 font-medium">
              Powered by LangGraph + Neo4j + ChromaDB
            </span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold leading-tight mb-6">
            <span className="gradient-text">LexOrch-KG</span>
          </h1>
          <h2 className="text-2xl md:text-3xl font-semibold text-dark-200 mb-4 max-w-4xl mx-auto">
            Explainable Agentic Legal Reasoning
          </h2>
          <p className="text-lg text-dark-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            AI-powered judicial decision support using multi-agent orchestration,
            knowledge graphs, and transparent reasoning — designed for legal professionals.
          </p>

          {/* Disclaimer */}
          <div className="disclaimer-banner max-w-2xl mx-auto mb-10 text-left">
            <Shield className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>
              <strong>Important:</strong> LexOrch-KG is a decision <em>support</em> tool only.
              All recommendations require review by qualified human legal professionals.
              This system does not replace judges, lawyers, or legal advisors.
            </span>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register" className="btn-primary text-base px-8 py-3.5">
              Start Analyzing Cases <ChevronRight className="w-5 h-5" />
            </Link>
            <Link to="/login" className="btn-secondary text-base px-8 py-3.5">
              Sign In to Platform
            </Link>
          </div>
        </div>
      </section>

      {/* ── Stats ──────────────────────────────────────────────── */}
      <section className="py-12 border-y border-dark-700/30">
        <div className="max-w-5xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map(({ label, value }) => (
            <div key={label} className="text-center">
              <div className="text-4xl font-bold gradient-text mb-1">{value}</div>
              <div className="text-dark-400 text-sm">{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Agent Pipeline ──────────────────────────────────────── */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-3">
            8-Agent <span className="gradient-text">AI Pipeline</span>
          </h2>
          <p className="text-dark-400 text-center mb-12">
            Every case goes through a deterministic multi-agent workflow
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {agentSteps.map(({ step, name, color }) => (
              <div key={step} className="glass p-4 rounded-xl flex items-center gap-3 group hover:border-primary-500/30 transition-all">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold text-white flex-shrink-0"
                  style={{ background: color }}
                >
                  {step}
                </div>
                <span className="text-sm text-dark-300 group-hover:text-dark-100 transition-colors">
                  {name}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Features ────────────────────────────────────────────── */}
      <section className="py-20 px-6 bg-dark-900/30">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-3">
            Platform <span className="gradient-text">Capabilities</span>
          </h2>
          <p className="text-dark-400 text-center mb-12">
            Enterprise-grade legal AI with full explainability
          </p>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map(({ icon: Icon, color, title, desc }) => (
              <div key={title} className="card group animate-slide-up">
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${color} flex items-center justify-center mb-4`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <h3 className="font-semibold text-dark-100 mb-2">{title}</h3>
                <p className="text-dark-400 text-sm leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Workflow ─────────────────────────────────────────────── */}
      <section className="py-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-12">
            How It <span className="gradient-text">Works</span>
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: '01', icon: Upload, title: 'Upload Case', desc: 'Upload PDF, DOCX, or TXT legal documents. OCR handles scanned documents automatically.' },
              { step: '02', icon: Brain,  title: 'AI Analysis',  desc: '8 specialized agents analyze the case, build a knowledge graph, and retrieve relevant precedents.' },
              { step: '03', icon: FileText, title: 'Review & Export', desc: 'Human experts review AI recommendations and download professional PDF/JSON/HTML reports.' },
            ].map(({ step, icon: Icon, title, desc }) => (
              <div key={step} className="relative">
                <div className="text-6xl font-bold text-dark-800 mb-4">{step}</div>
                <div className="w-12 h-12 rounded-xl bg-primary-500/20 border border-primary-500/30 flex items-center justify-center mx-auto mb-4">
                  <Icon className="w-6 h-6 text-primary-400" />
                </div>
                <h3 className="font-semibold text-lg mb-2">{title}</h3>
                <p className="text-dark-400 text-sm leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────────── */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto text-center glass p-12 rounded-2xl glow-blue">
          <Scale className="w-12 h-12 text-primary-400 mx-auto mb-4" />
          <h2 className="text-3xl font-bold mb-4">
            Ready to Transform Legal Analysis?
          </h2>
          <p className="text-dark-400 mb-8">
            Join legal professionals using AI to support judicial decision-making
            with transparency, explainability, and accountability.
          </p>
          <Link to="/register" className="btn-primary text-base px-10 py-4">
            Get Started Free <ChevronRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────── */}
      <footer className="border-t border-dark-700/50 py-8 px-6 text-center text-dark-500 text-sm">
        <div className="flex items-center justify-center gap-2 mb-3">
          <Scale className="w-4 h-4" />
          <span className="font-semibold text-dark-400">LexOrch-KG v1.0.0</span>
        </div>
        <p className="max-w-2xl mx-auto">
          ⚠️ This system is a legal decision SUPPORT tool only. It does not replace qualified human legal professionals.
          All AI-generated recommendations require expert human review before any legal action.
        </p>
        <p className="mt-3 text-dark-600">
          © 2024 LexOrch-KG | Built with FastAPI · React · LangGraph · Neo4j · ChromaDB
        </p>
      </footer>
    </div>
  )
}
