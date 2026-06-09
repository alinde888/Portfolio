import { useState } from "react";
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";

// ── Mock data ────────────────────────────────────────────────────────────────

const revenueData = [
  { month: "Jan", revenue: 4200, expenses: 2800, profit: 1400 },
  { month: "Feb", revenue: 5800, expenses: 3100, profit: 2700 },
  { month: "Mar", revenue: 5200, expenses: 2900, profit: 2300 },
  { month: "Apr", revenue: 7100, expenses: 3400, profit: 3700 },
  { month: "May", revenue: 6500, expenses: 3200, profit: 3300 },
  { month: "Jun", revenue: 8900, expenses: 3800, profit: 5100 },
];

const trafficData = [
  { day: "Mon", visitors: 1240, conversions: 87 },
  { day: "Tue", visitors: 1890, conversions: 134 },
  { day: "Wed", visitors: 1650, conversions: 108 },
  { day: "Thu", visitors: 2100, conversions: 189 },
  { day: "Fri", visitors: 1980, conversions: 162 },
  { day: "Sat", visitors: 1200, conversions: 74 },
  { day: "Sun", visitors: 980,  conversions: 58  },
];

const channelData = [
  { name: "Organic",  value: 38 },
  { name: "Paid Ads", value: 27 },
  { name: "Social",   value: 20 },
  { name: "Referral", value: 15 },
];

const COLORS = ["#6366f1", "#22d3ee", "#f59e0b", "#10b981"];

const topPages = [
  { page: "/home",        views: 12480, bounce: "32%" },
  { page: "/pricing",     views: 8940,  bounce: "28%" },
  { page: "/features",    views: 6720,  bounce: "41%" },
  { page: "/blog/post-1", views: 5210,  bounce: "55%" },
  { page: "/contact",     views: 3890,  bounce: "19%" },
];

// ── Stat card ─────────────────────────────────────────────────────────────────

function StatCard({ title, value, change, icon, color }) {
  const positive = change >= 0;
  return (
    <div style={{
      background: "#1e1e2e", borderRadius: 14, padding: "20px 24px",
      flex: 1, minWidth: 180,
      boxShadow: "0 4px 24px rgba(0,0,0,0.3)",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ color: "#a1a1aa", fontSize: 13 }}>{title}</span>
        <span style={{
          background: color + "22", color, borderRadius: 8,
          padding: "4px 10px", fontSize: 18,
        }}>{icon}</span>
      </div>
      <div style={{ marginTop: 12, fontSize: 28, fontWeight: 700, color: "#f4f4f5" }}>
        {value}
      </div>
      <div style={{ marginTop: 6, fontSize: 13, color: positive ? "#10b981" : "#f43f5e" }}>
        {positive ? "▲" : "▼"} {Math.abs(change)}% vs last month
      </div>
    </div>
  );
}

// ── Main dashboard ────────────────────────────────────────────────────────────

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("overview");

  const tabs = ["overview", "traffic", "revenue"];

  return (
    <div style={{
      background: "#13131f", minHeight: "100vh", color: "#f4f4f5",
      fontFamily: "'Inter', sans-serif", padding: "32px 40px",
    }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700 }}>Analytics Dashboard</h1>
          <p style={{ margin: "4px 0 0", color: "#71717a", fontSize: 14 }}>
            Last updated: {new Date().toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {tabs.map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} style={{
              background: activeTab === tab ? "#6366f1" : "#1e1e2e",
              color: activeTab === tab ? "#fff" : "#a1a1aa",
              border: "none", borderRadius: 8, padding: "8px 18px",
              cursor: "pointer", fontSize: 13, fontWeight: 600,
              textTransform: "capitalize",
            }}>{tab}</button>
          ))}
        </div>
      </div>

      {/* Stat cards */}
      <div style={{ display: "flex", gap: 16, marginBottom: 32, flexWrap: "wrap" }}>
        <StatCard title="Total Revenue"    value="$38,700"  change={12.4} icon="💰" color="#10b981" />
        <StatCard title="Monthly Visitors" value="11,040"   change={7.8}  icon="👥" color="#6366f1" />
        <StatCard title="Conversions"      value="812"      change={-3.2} icon="🎯" color="#f59e0b" />
        <StatCard title="Avg. Order Value" value="$47.60"   change={5.1}  icon="🛒" color="#22d3ee" />
      </div>

      {/* Charts row */}
      {(activeTab === "overview" || activeTab === "revenue") && (
        <div style={{ display: "flex", gap: 20, marginBottom: 24, flexWrap: "wrap" }}>
          {/* Revenue line chart */}
          <div style={{
            background: "#1e1e2e", borderRadius: 14, padding: 24,
            flex: 2, minWidth: 320, boxShadow: "0 4px 24px rgba(0,0,0,0.3)",
          }}>
            <h2 style={{ margin: "0 0 20px", fontSize: 16, fontWeight: 600 }}>Revenue vs Expenses</h2>
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={revenueData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2d2d3d" />
                <XAxis dataKey="month" stroke="#71717a" tick={{ fontSize: 12 }} />
                <YAxis stroke="#71717a" tick={{ fontSize: 12 }} tickFormatter={v => `$${v/1000}k`} />
                <Tooltip
                  contentStyle={{ background: "#13131f", border: "1px solid #2d2d3d", borderRadius: 8 }}
                  formatter={v => [`$${v.toLocaleString()}`, ""]}
                />
                <Legend />
                <Line type="monotone" dataKey="revenue"  stroke="#6366f1" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="expenses" stroke="#f43f5e" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="profit"   stroke="#10b981" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Channel pie chart */}
          <div style={{
            background: "#1e1e2e", borderRadius: 14, padding: 24,
            flex: 1, minWidth: 240, boxShadow: "0 4px 24px rgba(0,0,0,0.3)",
          }}>
            <h2 style={{ margin: "0 0 20px", fontSize: 16, fontWeight: 600 }}>Traffic Sources</h2>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={channelData} cx="50%" cy="50%" innerRadius={55} outerRadius={85}
                     dataKey="value" paddingAngle={3}>
                  {channelData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: "#13131f", border: "1px solid #2d2d3d", borderRadius: 8 }}
                  formatter={v => [`${v}%`, ""]}
                />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 8 }}>
              {channelData.map((d, i) => (
                <span key={d.name} style={{ fontSize: 12, color: COLORS[i], display: "flex", alignItems: "center", gap: 4 }}>
                  <span style={{ width: 8, height: 8, borderRadius: "50%", background: COLORS[i], display: "inline-block" }} />
                  {d.name} {d.value}%
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Traffic bar chart */}
      {(activeTab === "overview" || activeTab === "traffic") && (
        <div style={{ display: "flex", gap: 20, flexWrap: "wrap" }}>
          <div style={{
            background: "#1e1e2e", borderRadius: 14, padding: 24,
            flex: 2, minWidth: 320, boxShadow: "0 4px 24px rgba(0,0,0,0.3)",
          }}>
            <h2 style={{ margin: "0 0 20px", fontSize: 16, fontWeight: 600 }}>Weekly Traffic</h2>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={trafficData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2d2d3d" />
                <XAxis dataKey="day" stroke="#71717a" tick={{ fontSize: 12 }} />
                <YAxis stroke="#71717a" tick={{ fontSize: 12 }} />
                <Tooltip contentStyle={{ background: "#13131f", border: "1px solid #2d2d3d", borderRadius: 8 }} />
                <Legend />
                <Bar dataKey="visitors"    fill="#6366f1" radius={[4,4,0,0]} />
                <Bar dataKey="conversions" fill="#22d3ee" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Top pages table */}
          <div style={{
            background: "#1e1e2e", borderRadius: 14, padding: 24,
            flex: 1, minWidth: 260, boxShadow: "0 4px 24px rgba(0,0,0,0.3)",
          }}>
            <h2 style={{ margin: "0 0 16px", fontSize: 16, fontWeight: 600 }}>Top Pages</h2>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
              <thead>
                <tr style={{ color: "#71717a", borderBottom: "1px solid #2d2d3d" }}>
                  <th style={{ textAlign: "left",  padding: "0 0 10px" }}>Page</th>
                  <th style={{ textAlign: "right", padding: "0 0 10px" }}>Views</th>
                  <th style={{ textAlign: "right", padding: "0 0 10px" }}>Bounce</th>
                </tr>
              </thead>
              <tbody>
                {topPages.map(p => (
                  <tr key={p.page} style={{ borderBottom: "1px solid #2d2d3d" }}>
                    <td style={{ padding: "10px 0", color: "#a1a1aa" }}>{p.page}</td>
                    <td style={{ padding: "10px 0", textAlign: "right" }}>{p.views.toLocaleString()}</td>
                    <td style={{ padding: "10px 0", textAlign: "right", color: parseInt(p.bounce) > 50 ? "#f43f5e" : "#10b981" }}>
                      {p.bounce}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
