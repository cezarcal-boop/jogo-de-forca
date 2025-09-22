// Config
const ARQUIVO_BANCO = "banco_palavras.json";
const MAX_ERROS = 6;

const $ = (s) => document.querySelector(s);
const temaSelect = $("#temaSelect");
const nivelSelect = $("#nivelSelect");
const novaBtn = $("#novaBtn");
const dicaBtn = $("#dicaBtn");
const chutarBtn = $("#chutarBtn");
const canvas = $("#forcaCanvas");
const ctx = canvas.getContext("2d");
const palavraEl = $("#palavra");
const dicaEl = $("#dica");
const tentadasEl = $("#tentadas");
const statusEl = $("#status");
const teclado = $("#teclado");

// Estado
let bancoPorTema = {};
let temas = [];
let usados = new Set(); // "tema|palavra"
let itemAtual = null;
let exibida = "";
let alvo = "";
let reveladas = [];
let tentadas = new Set();
let erros = 0;
let dicaMostrada = false;

// Util
function normalizar(txt){
  return (txt||"")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g,"")
    .toUpperCase()
    .replace(/[^A-Z]/g,"");
}
function keyTemaPalavra(tema, palavra){ return tema + "|" + palavra; }

// Desenho
function resetDesenho(){
  ctx.clearRect(0,0,canvas.width,canvas.height);
  ctx.lineWidth = 6; ctx.strokeStyle = "#111";
  ctx.beginPath(); ctx.moveTo(30,330); ctx.lineTo(190,330); ctx.stroke(); // base
  ctx.beginPath(); ctx.moveTo(70,330); ctx.lineTo(70,40); ctx.stroke();  // poste
  ctx.beginPath(); ctx.moveTo(70,40); ctx.lineTo(230,40); ctx.stroke();  // viga
  ctx.beginPath(); ctx.moveTo(230,40); ctx.lineTo(230,80); ctx.stroke(); // corda
}
function desenharParte(n){
  ctx.lineWidth = 4; ctx.strokeStyle = "#111";
  if (n>=1){ ctx.beginPath(); ctx.arc(230,105,25,0,Math.PI*2); ctx.stroke(); }       // cabeca
  if (n>=2){ ctx.beginPath(); ctx.moveTo(230,130); ctx.lineTo(230,200); ctx.stroke(); } // tronco
  if (n>=3){ ctx.beginPath(); ctx.moveTo(230,150); ctx.lineTo(200,175); ctx.stroke(); } // braco esq
  if (n>=4){ ctx.beginPath(); ctx.moveTo(230,150); ctx.lineTo(260,175); ctx.stroke(); } // braco dir
  if (n>=5){ ctx.beginPath(); ctx.moveTo(230,200); ctx.lineTo(205,250); ctx.stroke(); } // perna esq
  if (n>=6){ ctx.beginPath(); ctx.moveTo(230,200); ctx.lineTo(255,250); ctx.stroke(); } // perna dir
}
function atualizarPalavra(full){
  palavraEl.textContent = full ? exibida.split("").join(" ") : reveladas.join(" ");
}
function atualizarDica(force){
  dicaEl.textContent = (force || dicaMostrada || erros>=2) ? ("Dica: " + (itemAtual?.dica || "-")) : "Dica: -";
}
function atualizarTentadas(){
  tentadasEl.textContent = "Letras tentadas: " + (tentadas.size ? [...tentadas].sort().join(" ") : "-");
}
function infoStatus(msg){ statusEl.textContent = msg || ""; }

// Banco
async function carregarBanco(){
  const resp = await fetch(ARQUIVO_BANCO);
  const data = await resp.json();
  const palavras = data.palavras || [];
  bancoPorTema = {};
  for (const it of palavras){
    (bancoPorTema[it.tema] ||= []).push(it);
  }
  temas = Object.keys(bancoPorTema).sort();
  temaSelect.innerHTML = "";
  for (const t of [...temas, "ALEATORIO"]){
    const opt = document.createElement("option");
    opt.value = t; opt.textContent = t;
    temaSelect.appendChild(opt);
  }
  temaSelect.value = temas[0];
}

// Filtro e sorteio
function filtrar(tema, nivel){
  let base = bancoPorTema[tema] || [];
  if (nivel !== "TODOS"){ base = base.filter(x => (x.nivel||"A") === nivel); }
  let elegiveis = base.filter(x => !usados.has(keyTemaPalavra(x.tema, x.palavra_exibida)));
  if (!elegiveis.length){
    [...usados].forEach(k => { if (k.startsWith(tema + "|")) usados.delete(k); });
    elegiveis = base;
  }
  return elegiveis;
}
function novaPalavra(auto){
  const temaSel = (temaSelect.value === "ALEATORIO") ? temas[Math.floor(Math.random()*temas.length)] : temaSelect.value;
  const nivelSel = nivelSelect.value || "TODOS";
  const candidatos = filtrar(temaSel, nivelSel);
  if (!candidatos.length){ infoStatus("Sem palavras para esse filtro."); return; }

  itemAtual = candidatos[Math.floor(Math.random()*candidatos.length)];
  exibida = (itemAtual.palavra_exibida || "").toUpperCase();
  alvo = normalizar(exibida);

  reveladas = Array.from(exibida).map(c => /[A-Z]/i.test(normalizar(c)) ? "_" : c);
  tentadas = new Set();
  erros = 0;
  dicaMostrada = false;
  usados.add(keyTemaPalavra(itemAtual.tema, itemAtual.palavra_exibida));

  resetDesenho();
  atualizarPalavra(false);
  atualizarDica(false);
  atualizarTentadas();
  infoStatus(auto ? "" : "Nova palavra selecionada. Boa sorte!");
  habilitarTeclado(true);
}

// Teclado
function montarTeclado(){
  teclado.innerHTML = "";
  const letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  for (const ch of letras){
    const b = document.createElement("button");
    b.className = "kb-btn";
    b.textContent = ch;
    b.addEventListener("click", () => tentarLetra(ch, b));
    teclado.appendChild(b);
  }
}
function habilitarTeclado(status){
  teclado.querySelectorAll("button").forEach(b => b.disabled = !status);
}
function tentarLetra(ch, btn){
  const letra = normalizar(ch);
  if (!letra || letra.length !== 1) return;
  if (tentadas.has(letra)){ infoStatus("Voce ja tentou essa letra."); return; }

  tentadas.add(letra);
  atualizarTentadas();

  if (alvo.includes(letra)){
    const chars = exibida.split("");
    for (let i=0;i<chars.length;i++){
      if (normalizar(chars[i]) === letra) reveladas[i] = chars[i];
    }
    if (btn){ btn.classList.add("good"); btn.disabled = true; }
    infoStatus("Boa! Continue assim.");
    atualizarPalavra(false);
    if (!reveladas.includes("_")) vitoria();
  } else {
    erros++;
    if (btn){ btn.classList.add("bad"); btn.disabled = true; }
    infoStatus("Nao tem essa letra. Tente outra.");
    desenharParte(erros);
    if (erros >= MAX_ERROS) derrota();
  }
}
function chutarPalavra(){
  if (!itemAtual) return;
  const chute = prompt("Digite seu palpite para a palavra:");
  if (chute == null) return;
  if (normalizar(chute) === alvo){ vitoria(); }
  else {
    erros++; infoStatus("Quase! Nao foi desta vez.");
    desenharParte(erros);
    if (erros >= MAX_ERROS) derrota();
  }
}
function mostrarDica(){ dicaMostrada = true; atualizarDica(true); }

function vitoria(){
  habilitarTeclado(false);
  atualizarPalavra(true);
  alert("Parabens! Voce acertou: " + exibida);
  infoStatus("Vitoria! Clique em Nova palavra para continuar.");
}
function derrota(){
  habilitarTeclado(false);
  atualizarPalavra(true);
  alert("Boa tentativa! A palavra era: " + exibida);
  infoStatus("Fim das chances. Clique em Nova palavra para tentar outra.");
}

// Eventos
novaBtn.addEventListener("click", () => novaPalavra(false));
dicaBtn.addEventListener("click", mostrarDica);
chutarBtn.addEventListener("click", chutarPalavra);
document.addEventListener("keydown", (e)=>{
  const k = (e.key || "").toUpperCase();
  if (/^[A-Z]$/.test(k)){
    const btn = [...teclado.querySelectorAll("button")].find(b => b.textContent === k);
    if (btn && !btn.disabled) tentarLetra(k, btn);
  } else if (k === "ENTER"){
    novaPalavra(false);
  }
});

// Boot
(async function init(){
  montarTeclado();
  await carregarBanco();
  novaPalavra(true);
})();
