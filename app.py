# -*- coding: utf-8 -*-
"""
医院信息统计系统 (Hospital Information Statistics)
单文件 Flask 应用：患者信息管理 + 多维度统计（科室/性别/年龄/状态）
本地运行：  python app.py
部署上线：  打包整个文件夹（含 Dockerfile）到 CloudBase 云托管
"""
import os
import json
import uuid
from datetime import datetime

from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")

# 可选科室 / 状态，用于前端下拉与统计归类
DEPARTMENTS = ["内科", "外科", "儿科", "妇产科", "骨科", "急诊科", "眼科", "口腔科", "神经科", "心血管科"]
STATUSES = ["住院", "出院", "转院"]

# 演示用默认患者数据（替换成真实数据即可）
DEFAULT_PATIENTS = [
    {"name": "王建国", "gender": "男", "age": 58, "department": "心血管科", "diagnosis": "冠心病", "admission": "2026-11-01", "status": "住院"},
    {"name": "李秀兰", "gender": "女", "age": 34, "department": "妇产科", "diagnosis": "妊娠期糖尿病", "admission": "2026-11-02", "status": "住院"},
    {"name": "张伟", "gender": "男", "age": 12, "department": "儿科", "diagnosis": "急性扁桃体炎", "admission": "2026-11-03", "status": "出院"},
    {"name": "赵敏", "gender": "女", "age": 45, "department": "内科", "diagnosis": "高血压", "admission": "2026-11-03", "status": "住院"},
    {"name": "刘强", "gender": "男", "age": 67, "department": "骨科", "diagnosis": "股骨骨折", "admission": "2026-11-04", "status": "住院"},
    {"name": "陈静", "gender": "女", "age": 28, "department": "眼科", "diagnosis": "白内障", "admission": "2026-11-05", "status": "出院"},
    {"name": "杨光", "gender": "男", "age": 39, "department": "外科", "diagnosis": "阑尾炎", "admission": "2026-11-05", "status": "转院"},
    {"name": "周婷", "gender": "女", "age": 52, "department": "神经科", "diagnosis": "偏头痛", "admission": "2026-11-06", "status": "住院"},
    {"name": "吴磊", "gender": "男", "age": 8, "department": "儿科", "diagnosis": "手足口病", "admission": "2026-11-06", "status": "出院"},
    {"name": "郑霞", "gender": "女", "age": 71, "department": "心血管科", "diagnosis": "心律失常", "admission": "2026-11-07", "status": "住院"},
    {"name": "孙浩", "gender": "男", "age": 24, "department": "急诊科", "diagnosis": "急性肠胃炎", "admission": "2026-11-07", "status": "出院"},
    {"name": "马丽", "gender": "女", "age": 60, "department": "内科", "diagnosis": "糖尿病", "admission": "2026-11-08", "status": "住院"},
]


def load_data():
    if not os.path.exists(DATA_FILE):
        return [dict(p, id=str(uuid.uuid4())) for p in DEFAULT_PATIENTS]
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_data(patients):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(patients, f, ensure_ascii=False, indent=2)


patients = load_data()


def compute_stats(items):
    total = len(items)
    male = sum(1 for p in items if p.get("gender") == "男")
    female = total - male
    in_hospital = sum(1 for p in items if p.get("status") == "住院")

    by_dept = {}
    for p in items:
        by_dept[p.get("department", "未知")] = by_dept.get(p.get("department", "未知"), 0) + 1

    age_groups = {"0-18": 0, "19-35": 0, "36-50": 0, "51-65": 0, "65+": 0}
    for p in items:
        try:
            a = int(p.get("age", 0))
        except Exception:
            a = 0
        if a <= 18:
            age_groups["0-18"] += 1
        elif a <= 35:
            age_groups["19-35"] += 1
        elif a <= 50:
            age_groups["36-50"] += 1
        elif a <= 65:
            age_groups["51-65"] += 1
        else:
            age_groups["65+"] += 1

    by_status = {}
    for p in items:
        s = p.get("status", "未知")
        by_status[s] = by_status.get(s, 0) + 1

    return {
        "total": total,
        "male": male,
        "female": female,
        "in_hospital": in_hospital,
        "by_dept": by_dept,
        "age_groups": age_groups,
        "by_status": by_status,
    }


@app.route("/")
def index():
    return render_template_string(HTML, departments=DEPARTMENTS, statuses=STATUSES)


@app.route("/api/patients", methods=["GET"])
def get_patients():
    return jsonify(patients)


@app.route("/api/patients", methods=["POST"])
def add_patient():
    body = request.json or {}
    name = (body.get("name") or "").strip()
    if not name:
        return jsonify({"error": "姓名不能为空"}), 400
    try:
        age = int(body.get("age", 0))
    except Exception:
        return jsonify({"error": "年龄必须为数字"}), 400
    patient = {
        "id": str(uuid.uuid4()),
        "name": name,
        "gender": body.get("gender", "男"),
        "age": age,
        "department": body.get("department", DEPARTMENTS[0]),
        "diagnosis": (body.get("diagnosis") or "").strip(),
        "admission": body.get("admission") or datetime.now().strftime("%Y-%m-%d"),
        "status": body.get("status", STATUSES[0]),
    }
    patients.append(patient)
    save_data(patients)
    return jsonify(patient), 201


@app.route("/api/patients/<pid>", methods=["DELETE"])
def del_patient(pid):
    global patients
    patients = [p for p in patients if p.get("id") != pid]
    save_data(patients)
    return jsonify({"ok": True})


@app.route("/api/stats", methods=["GET"])
def get_stats():
    return jsonify(compute_stats(patients))


HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>医院信息统计系统</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
    background: linear-gradient(135deg, #0ea5a4 0%, #2563eb 100%);
    min-height: 100vh; color: #1f2937; padding: 24px;
  }
  .wrap { max-width: 1180px; margin: 0 auto; }
  h1 { color: #fff; text-align: center; font-size: 28px; letter-spacing: 2px; }
  .sub { color: rgba(255,255,255,.85); text-align: center; margin-bottom: 22px; font-size: 14px; }
  .cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }
  .cardbox { background: #fff; border-radius: 14px; padding: 18px; text-align: center; box-shadow: 0 8px 24px rgba(0,0,0,.15); }
  .cardbox b { display: block; font-size: 30px; color: #0ea5a4; }
  .cardbox span { font-size: 13px; color: #888; }
  .grid { display: grid; grid-template-columns: 1fr 1.2fr; gap: 18px; }
  @media (max-width: 900px){ .grid { grid-template-columns: 1fr; } .cards { grid-template-columns: repeat(2,1fr); } }
  .card { background: #fff; border-radius: 16px; padding: 20px; box-shadow: 0 8px 24px rgba(0,0,0,.15); }
  .card h2 { font-size: 17px; margin-bottom: 14px; display:flex; justify-content:space-between; align-items:center; }
  .count { background:#0ea5a4; color:#fff; border-radius:20px; padding:2px 10px; font-size:13px; }
  label { display:block; font-size:12px; color:#666; margin:10px 0 4px; }
  input, select {
    width:100%; padding:9px 11px; border:1px solid #ddd; border-radius:9px; font-size:14px; outline:none; background:#fff;
  }
  input:focus, select:focus { border-color:#0ea5a4; }
  .form-row { display:grid; grid-template-columns:1fr 1fr; gap:10px; }
  button { cursor:pointer; border:none; border-radius:10px; font-size:14px; padding:10px 14px; transition:.15s; }
  .btn-primary { background:#0ea5a4; color:#fff; width:100%; margin-top:14px; }
  .btn-primary:hover { background:#0c8f8e; }
  .btn-ghost { background:#f0f0f5; color:#555; }
  .btn-ghost:hover { background:#e4e4ee; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th, td { text-align:left; padding:8px 6px; border-bottom:1px solid #f0f0f5; }
  th { color:#999; font-weight:600; position:sticky; top:0; background:#fff; }
  .table-scroll { max-height:340px; overflow:auto; }
  .del { background:#ffe3e3; color:#e23b3b; border-radius:8px; padding:4px 10px; font-size:13px; }
  .del:hover { background:#ffd0d0; }
  .tag { padding:2px 8px; border-radius:6px; font-size:12px; }
  .tag-in { background:#e6f9ed; color:#1a9e4f; }
  .tag-out { background:#e6f0ff; color:#2563eb; }
  .tag-trans { background:#fff4e0; color:#d98a00; }
  .bar-block { margin-bottom:14px; }
  .bar-label { display:flex; justify-content:space-between; font-size:13px; margin-bottom:4px; }
  .bar-track { background:#f0f0f5; border-radius:8px; height:18px; overflow:hidden; }
  .bar-fill { height:100%; background:linear-gradient(90deg,#0ea5a4,#2563eb); border-radius:8px; transition:width .4s; }
  .empty { color:#bbb; text-align:center; padding:24px 0; font-size:14px; }
  .legend { font-size:12px; color:#888; margin-top:6px; }
</style>
</head>
<body>
<div class="wrap">
  <h1>医院信息统计系统</h1>
  <div class="sub">Hospital Information Statistics</div>

  <div class="cards">
    <div class="cardbox"><b id="stTotal">0</b><span>患者总数</span></div>
    <div class="cardbox"><b id="stMale">0</b><span>男性</span></div>
    <div class="cardbox"><b id="stFemale">0</b><span>女性</span></div>
    <div class="cardbox"><b id="stIn">0</b><span>在院</span></div>
  </div>

  <div class="grid">
    <!-- 患者管理 -->
    <div class="card">
      <h2>患者管理 <span class="count" id="count">0 人</span></h2>
      <label>姓名</label>
      <input type="text" id="f_name" placeholder="请输入患者姓名">
      <div class="form-row">
        <div><label>性别</label><select id="f_gender"><option>男</option><option>女</option></select></div>
        <div><label>年龄</label><input type="number" id="f_age" placeholder="年龄" min="0"></div>
      </div>
      <div class="form-row">
        <div><label>科室</label><select id="f_dept"></select></div>
        <div><label>状态</label><select id="f_status"></select></div>
      </div>
      <label>诊断</label>
      <input type="text" id="f_diag" placeholder="如：高血压、骨折…">
      <label>入院日期</label>
      <input type="date" id="f_date">
      <button class="btn-primary" onclick="addPatient()">添加患者</button>

      <div class="table-scroll" style="margin-top:16px;">
        <table>
          <thead><tr><th>姓名</th><th>性别</th><th>年龄</th><th>科室</th><th>状态</th><th></th></tr></thead>
          <tbody id="ptBody"></tbody>
        </table>
      </div>
    </div>

    <!-- 统计 -->
    <div class="card">
      <h2>统计看板</h2>
      <h3 style="font-size:14px;color:#555;margin:6px 0;">科室分布</h3>
      <div id="chartDept"></div>
      <h3 style="font-size:14px;color:#555;margin:16px 0 6px;">年龄段分布</h3>
      <div id="chartAge"></div>
      <h3 style="font-size:14px;color:#555;margin:16px 0 6px;">就诊状态</h3>
      <div id="chartStatus"></div>
    </div>
  </div>
</div>

<script>
const DEPTS = {{ departments | tojson }};
const STATUSES = {{ statuses | tojson }};

// 初始化下拉
DEPTS.forEach(d => { const o=document.createElement('option'); o.value=d; o.textContent=d; document.getElementById('f_dept').appendChild(o); });
STATUSES.forEach(s => { const o=document.createElement('option'); o.value=s; o.textContent=s; document.getElementById('f_status').appendChild(o); });
document.getElementById('f_date').value = new Date().toISOString().slice(0,10);

const STATUS_CLASS = { '住院':'tag-in', '出院':'tag-out', '转院':'tag-trans' };

async function loadAll(){
  const [ps, st] = await Promise.all([
    fetch('/api/patients').then(r=>r.json()),
    fetch('/api/stats').then(r=>r.json())
  ]);
  // 概览卡
  document.getElementById('stTotal').textContent = st.total;
  document.getElementById('stMale').textContent = st.male;
  document.getElementById('stFemale').textContent = st.female;
  document.getElementById('stIn').textContent = st.in_hospital;
  document.getElementById('count').textContent = st.total + ' 人';
  // 列表
  const tb = document.getElementById('ptBody');
  tb.innerHTML = '';
  if(ps.length === 0){ tb.innerHTML = '<tr><td colspan="6" class="empty">暂无患者，先在左侧添加</td></tr>'; }
  ps.forEach(p=>{
    const cls = STATUS_CLASS[p.status] || 'tag-out';
    tb.innerHTML += `<tr><td>${p.name}</td><td>${p.gender}</td><td>${p.age}</td><td>${p.department}</td><td><span class="tag ${cls}">${p.status}</span></td><td><button class="del" onclick="delPatient('${p.id}')">删除</button></td></tr>`;
  });
  // 图表
  renderBars('chartDept', st.by_dept);
  renderBars('chartAge', st.age_groups);
  renderBars('chartStatus', st.by_status);
}

function renderBars(elId, obj){
  const entries = Object.entries(obj).sort((a,b)=>b[1]-a[1]);
  const max = entries.reduce((m,e)=>Math.max(m,e[1]),0) || 1;
  const el = document.getElementById(elId);
  if(entries.length === 0 || max === 0){ el.innerHTML = '<div class="empty">暂无数据</div>'; return; }
  el.innerHTML = entries.map(([k,v])=>`
    <div class="bar-block">
      <div class="bar-label"><span>${k}</span><span>${v} 人</span></div>
      <div class="bar-track"><div class="bar-fill" style="width:${Math.round(v/max*100)}%"></div></div>
    </div>`).join('');
}

async function addPatient(){
  const payload = {
    name: document.getElementById('f_name').value.trim(),
    gender: document.getElementById('f_gender').value,
    age: document.getElementById('f_age').value,
    department: document.getElementById('f_dept').value,
    diagnosis: document.getElementById('f_diag').value.trim(),
    admission: document.getElementById('f_date').value,
    status: document.getElementById('f_status').value,
  };
  if(!payload.name){ alert('请输入姓名'); return; }
  const res = await fetch('/api/patients', {
    method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)
  });
  if(!res.ok){ const e = await res.json(); alert(e.error); return; }
  document.getElementById('f_name').value='';
  document.getElementById('f_diag').value='';
  document.getElementById('f_age').value='';
  loadAll();
}

async function delPatient(id){
  if(!confirm('确定删除该患者？')) return;
  await fetch('/api/patients/'+id, {method:'DELETE'});
  loadAll();
}

loadAll();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
