import React, { useState, useEffect } from "react";
import { 
  ShieldAlert, ShieldCheck, Activity, UploadCloud, 
  Filter, AlertTriangle, Trash2, User, LogOut, Search 
} from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";

const API_BASE = "http://127.0.0.1:8000/api";
const SEVERITY_COLORS = { Critique: "#ef4444", Haute: "#f97316", Moyenne: "#eab308" };

export default function App() {
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState("signin");
  const [authForm, setAuthForm] = useState({ username: "", password: "" });
  const [authError, setAuthError] = useState("");

  const [stats, setStats] = useState({ totals: {}, by_severity: {} });
  const [alerts, setAlerts] = useState([]);
  const [analyses, setAnalyses] = useState([]);
  const [selectedSeverity, setSelectedSeverity] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("");
  const [ipFilter, setIpFilter] = useState("");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  const reloadAll = () => {
    fetchStats();
    fetchAlerts();
    fetchAnalyses();
  };

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/dashboard-stats`);
      if (res.ok) setStats(await res.json());
    } catch (e) { console.error(e); }
  };

  const fetchAnalyses = async () => {
    try {
      const res = await fetch(`${API_BASE}/analyses`);
      if (res.ok) setAnalyses(await res.json());
    } catch (e) { console.error(e); }
  };

  const fetchAlerts = async () => {
    try {
      let url = `${API_BASE}/alerts?limit=50`;
      if (selectedSeverity) url += `&severity=${selectedSeverity}`;
      if (selectedStatus) url += `&status=${selectedStatus}`;
      if (ipFilter) url += `&ip=${encodeURIComponent(ipFilter)}`;
      const res = await fetch(url);
      if (res.ok) setAlerts(await res.json());
    } catch (e) { console.error(e); }
  };

  useEffect(() => {
    reloadAll();
  }, [selectedSeverity, selectedStatus, ipFilter]);

  const handleAuth = async (e) => {
    e.preventDefault();
    setAuthError("");
    const endpoint = authMode === "signin" ? "/auth/login" : "/auth/signup";
    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(authForm)
      });
      const data = await res.json();
      if (!res.ok) {
        setAuthError(data.detail || "Erreur d'authentification.");
      } else {
        if (authMode === "signup") {
          setAuthMode("signin");
          setAuthError("Compte créé ! Veuillez vous connecter.");
        } else {
          setUser(data.username);
        }
      }
    } catch (err) {
      setAuthError("Serveur d'authentification inaccessible.");
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setErrorMessage("");
    setUploadResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/predict-file`, { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) {
        setErrorMessage(data.detail || "Erreur lors de l'analyse.");
      } else {
        setUploadResult(data);
        reloadAll();
      }
    } catch (err) {
      setErrorMessage("Impossible de contacter le serveur backend.");
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteAnalysis = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/analyses/${id}`, { method: "DELETE" });
      if (res.ok) reloadAll();
    } catch (err) { console.error(err); }
  };

  const handleStatusChange = async (alertId, newStatus) => {
    try {
      const res = await fetch(`${API_BASE}/alerts/${alertId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus })
      });
      if (res.ok) reloadAll();
    } catch (err) { console.error(err); }
  };

  const pieData = Object.keys(stats.by_severity || {}).map((k) => ({
    name: k,
    value: stats.by_severity[k]
  }));

  // Vue Login / Register si déconnecté
  if (!user) {
    return (
      <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "80vh" }}>
        <div style={{ background: "#1e293b", padding: "2.5rem", borderRadius: "12px", border: "1px solid #334155", width: "360px" }}>
          <h2 style={{ textAlign: "center", color: "#38bdf8", marginBottom: "1.5rem" }}>
            {authMode === "signin" ? "Connexion SOC" : "Inscription SOC"}
          </h2>
          <form onSubmit={handleAuth}>
            <div style={{ marginBottom: "1rem" }}>
              <label style={{ display: "block", color: "#94a3b8", fontSize: "0.85rem", marginBottom: "0.4rem" }}>Utilisateur</label>
              <input 
                type="text" 
                required
                value={authForm.username}
                onChange={(e) => setAuthForm({ ...authForm, username: e.target.value })}
                style={{ width: "100%", padding: "0.6rem", background: "#0f172a", border: "1px solid #475569", borderRadius: "6px", color: "#f8fafc" }}
              />
            </div>
            <div style={{ marginBottom: "1.5rem" }}>
              <label style={{ display: "block", color: "#94a3b8", fontSize: "0.85rem", marginBottom: "0.4rem" }}>Mot de passe</label>
              <input 
                type="password" 
                required
                value={authForm.password}
                onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
                style={{ width: "100%", padding: "0.6rem", background: "#0f172a", border: "1px solid #475569", borderRadius: "6px", color: "#f8fafc" }}
              />
            </div>
            {authError && <p style={{ color: "#f87171", fontSize: "0.85rem", marginBottom: "1rem" }}>{authError}</p>}
            <button type="submit" style={{ width: "100%", padding: "0.7rem", background: "#0284c7", border: "none", color: "#fff", borderRadius: "6px", fontWeight: "bold", cursor: "pointer" }}>
              {authMode === "signin" ? "Se connecter" : "S'enregistrer"}
            </button>
          </form>
          <p style={{ textAlign: "center", color: "#94a3b8", fontSize: "0.85rem", marginTop: "1rem" }}>
            {authMode === "signin" ? "Pas encore de compte ? " : "Déjà un compte ? "}
            <span 
              onClick={() => { setAuthMode(authMode === "signin" ? "signup" : "signin"); setAuthError(""); }}
              style={{ color: "#38bdf8", cursor: "pointer", textDecoration: "underline" }}
            >
              {authMode === "signin" ? "Créer un compte" : "Se connecter"}
            </span>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: "2rem", maxWidth: "1300px", margin: "0 auto" }}>
      {/* Header avec état utilisateur */}
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "2rem" }}>
        <div>
          <h1 style={{ display: "flex", alignItems: "center", gap: "0.75rem", fontSize: "1.8rem", color: "#38bdf8" }}>
            <Activity /> AI-Powered NIDS Dashboard
          </h1>
          <p style={{ color: "#94a3b8" }}>Surveillance & Détection par Random Forest (UNSW-NB15)</p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <span style={{ display: "flex", alignItems: "center", gap: "0.4rem", color: "#cbd5e1" }}>
            <User size={18} color="#38bdf8" /> {user}
          </span>
          <button 
            onClick={() => setUser(null)}
            style={{ display: "flex", alignItems: "center", gap: "0.4rem", background: "#ef444422", border: "1px solid #ef4444", color: "#fca5a5", padding: "0.5rem 0.8rem", borderRadius: "6px", cursor: "pointer" }}
          >
            <LogOut size={16} /> Déconnexion
          </button>
        </div>
      </header>

      {/* KPI Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "1.2rem", marginBottom: "2rem" }}>
        <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "#94a3b8" }}>
            <span>Total Flux Inspectés</span>
            <Activity size={20} color="#38bdf8" />
          </div>
          <p style={{ fontSize: "2rem", fontWeight: "bold", marginTop: "0.5rem", color: "#f8fafc" }}>{stats.totals?.total_flows || 0}</p>
        </div>
        <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "#94a3b8" }}>
            <span>Trafic Normal</span>
            <ShieldCheck size={20} color="#22c55e" />
          </div>
          <p style={{ fontSize: "2rem", fontWeight: "bold", marginTop: "0.5rem", color: "#22c55e" }}>{stats.totals?.normal_flows || 0}</p>
        </div>
        <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <div style={{ display: "flex", justifyContent: "space-between", color: "#94a3b8" }}>
            <span>Alertes Identifiées</span>
            <ShieldAlert size={20} color="#ef4444" />
          </div>
          <p style={{ fontSize: "2rem", fontWeight: "bold", marginTop: "0.5rem", color: "#ef4444" }}>{stats.totals?.alert_flows || 0}</p>
        </div>
      </div>

      {/* Section Import & Fichiers déjà soumis */}
      <div style={{ display: "grid", gridTemplateColumns: "1.2fr 1fr", gap: "1.5rem", marginBottom: "2rem" }}>
        <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <h2 style={{ fontSize: "1.1rem", marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <UploadCloud color="#38bdf8" /> Téléverser un flux de capture (CSV)
          </h2>
          <form onSubmit={handleUpload}>
            <input 
              type="file" 
              accept=".csv" 
              onChange={(e) => setFile(e.target.files[0])}
              style={{ display: "block", width: "100%", padding: "0.5rem", background: "#0f172a", border: "1px dashed #475569", borderRadius: "6px", color: "#cbd5e1", marginBottom: "0.8rem" }}
            />
            <button 
              type="submit" 
              disabled={!file || uploading}
              style={{ background: "#0284c7", color: "#fff", border: "none", padding: "0.6rem 1.2rem", borderRadius: "6px", cursor: file && !uploading ? "pointer" : "not-allowed", width: "100%", fontWeight: "600" }}
            >
              {uploading ? "Inférence par l'IA..." : "Analyser le fichier"}
            </button>
          </form>

          {errorMessage && (
            <div style={{ marginTop: "1rem", padding: "0.6rem", background: "rgba(239, 68, 68, 0.15)", border: "1px solid #ef4444", borderRadius: "6px", color: "#fca5a5", display: "flex", gap: "0.5rem" }}>
              <AlertTriangle size={18} /> {errorMessage}
            </div>
          )}
          {uploadResult && (
            <div style={{ marginTop: "1rem", padding: "0.6rem", background: "rgba(34, 197, 94, 0.15)", border: "1px solid #22c55e", borderRadius: "6px", color: "#86efac" }}>
              Terminé : <strong>{uploadResult.alert_flows}</strong> alertes sur {uploadResult.total_flows} flux.
            </div>
          )}

          {/* Liste des fichiers soumis avec bouton pour supprimer */}
          <h3 style={{ fontSize: "0.95rem", color: "#94a3b8", marginTop: "1.5rem", marginBottom: "0.6rem" }}>Fichiers injectés en mémoire :</h3>
          <div style={{ maxHeight: "140px", overflowY: "auto" }}>
            {analyses.map((a) => (
              <div key={a.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "#0f172a", padding: "0.4rem 0.8rem", borderRadius: "4px", marginBottom: "0.4rem", fontSize: "0.85rem" }}>
                <span>{a.filename} ({a.total_flows} flux) - {a.timestamp}</span>
                <button 
                  onClick={() => handleDeleteAnalysis(a.id)}
                  title="Enlever ce fichier et ses alertes"
                  style={{ background: "none", border: "none", color: "#f87171", cursor: "pointer" }}
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Répartition des sévérités */}
        <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <h2 style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>Distribution des Sévérités</h2>
          {pieData.length > 0 ? (
            <div style={{ width: "100%", height: 230 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} dataKey="value">
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={SEVERITY_COLORS[entry.name] || "#94a3b8"} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p style={{ color: "#64748b", textAlign: "center", marginTop: "4rem" }}>Aucune alerte enregistrée.</p>
          )}
        </div>
      </div>

      {/* Journal des alertes avec filtre IP */}
      <div style={{ background: "#1e293b", padding: "1.5rem", borderRadius: "10px", border: "1px solid #334155" }}>
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "1rem", marginBottom: "1.2rem" }}>
          <h2 style={{ fontSize: "1.1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Filter size={18} /> Journal d'Investigation SOC
          </h2>

          <div style={{ display: "flex", gap: "0.8rem", alignItems: "center" }}>
            {/* Barre de recherche IP */}
            <div style={{ display: "flex", alignItems: "center", background: "#0f172a", border: "1px solid #334155", borderRadius: "6px", padding: "0.2rem 0.6rem" }}>
              <Search size={16} color="#94a3b8" />
              <input 
                type="text" 
                placeholder="Filtrer par IP..." 
                value={ipFilter}
                onChange={(e) => setIpFilter(e.target.value)}
                style={{ background: "transparent", border: "none", color: "#f8fafc", padding: "0.3rem 0.5rem", outline: "none", fontSize: "0.85rem" }}
              />
            </div>

            <select 
              value={selectedSeverity} 
              onChange={(e) => setSelectedSeverity(e.target.value)}
              style={{ background: "#0f172a", border: "1px solid #334155", color: "#e2e8f0", padding: "0.4rem 0.6rem", borderRadius: "6px" }}
            >
              <option value="">Toutes sévérités</option>
              <option value="Critique">Critique</option>
              <option value="Haute">Haute</option>
              <option value="Moyenne">Moyenne</option>
            </select>

            <select 
              value={selectedStatus} 
              onChange={(e) => setSelectedStatus(e.target.value)}
              style={{ background: "#0f172a", border: "1px solid #334155", color: "#e2e8f0", padding: "0.4rem 0.6rem", borderRadius: "6px" }}
            >
              <option value="">Tous statuts</option>
              <option value="Nouvelle">Nouvelle</option>
              <option value="Examinée">Examinée</option>
              <option value="Clôturée">Clôturée</option>
            </select>
          </div>
        </div>

        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left", fontSize: "0.88rem" }}>
          <thead>
            <tr style={{ borderBottom: "1px solid #334155", color: "#94a3b8" }}>
              <th style={{ padding: "0.6rem" }}>ID</th>
              <th style={{ padding: "0.6rem" }}>Horodatage</th>
              <th style={{ padding: "0.6rem" }}>Flux Source → Destination</th>
              
              <th style={{ padding: "0.6rem" }}>Sévérité / Certitude</th>
              <th style={{ padding: "0.6rem" }}>Statut</th>
              <th style={{ padding: "0.6rem" }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {alerts.length > 0 ? (
              alerts.map((al) => (
                <tr key={al.id} style={{ borderBottom: "1px solid #1e293b" }}>
                  <td style={{ padding: "0.6rem" }}>#{al.id}</td>
                  <td style={{ padding: "0.6rem" }}>{al.timestamp}</td>
                  <td style={{ padding: "0.6rem", fontFamily: "monospace" }}>
  <span style={{ color: "#38bdf8" }}>{al.src_ip}</span> → <span style={{ color: "#a5b4fc" }}>{al.dst_ip}</span> (Flux {al.flow_index})
</td>
                  <td style={{ padding: "0.6rem" }}>
                    <span style={{ 
                      padding: "0.2rem 0.5rem", 
                      borderRadius: "10px", 
                      fontSize: "0.75rem",
                      fontWeight: "bold",
                      background: `${SEVERITY_COLORS[al.severity]}22`,
                      color: SEVERITY_COLORS[al.severity]
                    }}>
                      {al.severity} ({al.confidence}%)
                    </span>
                  </td>
                  <td style={{ padding: "0.6rem" }}>{al.status}</td>
                  <td style={{ padding: "0.6rem" }}>
                    <select
                      value={al.status}
                      onChange={(e) => handleStatusChange(al.id, e.target.value)}
                      style={{ background: "#0f172a", border: "1px solid #475569", color: "#cbd5e1", borderRadius: "4px", padding: "0.2rem 0.3rem" }}
                    >
                      <option value="Nouvelle">Nouvelle</option>
                      <option value="Examinée">Examinée</option>
                      <option value="Clôturée">Clôturée</option>
                    </select>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="6" style={{ textAlign: "center", padding: "2rem", color: "#64748b" }}>
                  Aucune alerte correspondant aux critères de recherche.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}