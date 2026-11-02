
window.addEventListener("unhandledrejection", function(ev){
  try{
    var m = (ev.reason && (ev.reason.message || ev.reason)) || "";
    if(!m) return;
    if(window.avisar) window.avisar.erro("Algo falhou: " + m);
    else console.error("[ATS]", m);
  }catch(e){}
});

(function(){
  function faltando(){
    var f=[];
    if(typeof React==="undefined") f.push("React");
    if(typeof ReactDOM==="undefined") f.push("ReactDOM");
    if(typeof Babel==="undefined") f.push("Babel");
    return f;
  }
  window.addEventListener("load", function(){
    setTimeout(function(){
      var raiz=document.getElementById("root");
      if(raiz && raiz.children.length) return;
      var f=faltando();
      var causa = f.length
        ? "Nao foi possivel carregar: <b>"+f.join(", ")+"</b>."
        : "As bibliotecas carregaram, mas a tela nao desenhou. Provavelmente ha um erro no codigo.";
      var dica = f.length
        ? "<li>Rode o <b>baixar_bibliotecas.bat</b> uma vez, num computador com internet. Depois disso o sistema nao depende mais de sites externos.</li>"
          +"<li>Se ja rodou, confira se existe a pasta <b>app/static/vendor</b> com 5 arquivos .js dentro.</li>"
          +"<li>Enquanto isso, o sistema tenta a internet: a rede da empresa pode estar bloqueando <b>unpkg.com</b>.</li>"
        : "<li>Aperte F12, abra a aba <b>Console</b> e mande o erro em vermelho para o TI.</li>";
      raiz.innerHTML =
        '<div style="max-width:640px;margin:12vh auto;padding:28px;font-family:system-ui,sans-serif;'
        +'background:#fff;border:1px solid #eae7e2;border-radius:16px;box-shadow:0 8px 30px -12px rgba(28,25,23,.18)">'
        +'<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px">'
        +'<div style="width:40px;height:40px;border-radius:12px;background:#fef2f2;color:#dc2626;display:flex;'
        +'align-items:center;justify-content:center;font-weight:700;font-size:20px">!</div>'
        +'<div><div style="font-size:18px;font-weight:700;color:#1c1917">O sistema nao conseguiu abrir</div>'
        +'<div style="font-size:13px;color:#a8a29e">Seus dados estao a salvo no servidor</div></div></div>'
        +'<p style="font-size:14px;color:#57534e;line-height:1.6;margin:0 0 12px">'+causa+'</p>'
        +'<ul style="font-size:13.5px;color:#57534e;line-height:1.75;margin:0 0 18px;padding-left:20px">'+dica+'</ul>'
        +'<button onclick="location.reload()" style="background:#1c1917;color:#fff;border:0;padding:9px 16px;'
        +'border-radius:9px;font-weight:600;font-size:13.5px;cursor:pointer">Tentar de novo</button></div>';
    }, 3500);
  });
})();
