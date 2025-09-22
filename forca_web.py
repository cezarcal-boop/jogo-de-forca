<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Jogo da Forca : Versão Web</title>
  <link rel="stylesheet" href="style.css" />
</head>
<body>
  <header class="topbar">
    <h1>Jogo da Forca <span class="badge">web</span></h1>
  </header>

  <main class="container">
    <section class="controls">
      <label>
        Tema:
        <select id="temaSelect"></select>
      </label>

      <label>
        Nível:
        <select id="nivelSelect">
          <option value="TODOS">Todos</option>
          <option value="A">A (fácil)</option>
          <option value="B">B (médio)</option>
          <option value="C">C (desafio)</option>
        </select>
      </label>

      <button id="novaBtn" class="btn">Nova palavra</button>
      <button id="dicaBtn" class="btn alt">Dica</button>
      <button id="chutarBtn" class="btn warn">Chutar palavra</button>
    </section>

    <section class="game">
      <canvas id="forcaCanvas" width="360" height="360" aria-label="Desenho da forca"></canvas>

      <div class="panel">
        <div id="palavra" class="palavra">_ _ _ _</div>
        <div id="dica" class="dica">Dica: -</div>
        <div id="tentadas" class="tentadas">Letras tentadas: -</div>
        <div id="status" class="status"></div>

        <div class="teclado" id="teclado"></div>
      </div>
    </section>
  </main>

  <footer class="foot">
    <small>Educação Infantil : Funciona no navegador : Feito com carinho</small>
  </footer>

  <script src="app.js"></script>
</body>
</html>
