"""Long-term club investments in the actual Engine and in-scope club screen."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

MARKER = 'FUTBR_CLUB_MANAGEMENT_18374'

ENGINE = r'''  /* FUTBR_CLUB_MANAGEMENT_18374
   * Facilities belong to clubs. Only completed projects grant benefits.
   * No world/player scan: construction advances in the existing finance pass.
   */
  const MANAGEMENT18374={
    stadium:{name:'Estádio',icon:'club',base:1800000,upkeep:0},
    training:{name:'Centro de treinamento',icon:'tactics',base:1800000,upkeep:100000},
    youth:{name:'Categorias de base',icon:'spark',base:1400000,upkeep:68000},
    medical:{name:'Departamento médico',icon:'heart',base:1300000,upkeep:78000},
    scouting:{name:'Rede de olheiros',icon:'eye',base:900000,upkeep:32000},
    analytics:{name:'Análise de desempenho',icon:'chart',base:1100000,upkeep:38000},
    commercial:{name:'Comercial e marca',icon:'money',base:1600000,upkeep:45000},
    supporters:{name:'Experiência da torcida',icon:'users',base:1200000,upkeep:35000}
  };
  const PLANS18374={
    balanced:{name:'Equilíbrio',description:'Mantém os custos e o desenvolvimento habituais.',upkeep:1},
    development:{name:'Clube formador',description:'Desenvolvimento +10% até 23 anos e na base; -5% nos demais. Manutenção +5%.',upkeep:1.05},
    performance:{name:'Preparação física',description:'Recuperação +1,5 ponto de energia por jornada. Manutenção +10%.',upkeep:1.10},
    economy:{name:'Controle de custos',description:'Manutenção -15%; desenvolvimento -8% e recuperação -1 ponto por jornada.',upkeep:.85}
  };
  const STADIUM_CAPACITIES18374=[0,10000,18000,26000,36000,48000,60000,72000,84000,96000,108000,120000];
  function facilityLevel18374(t,key){
    if(!Object.hasOwn(MANAGEMENT18374,key))throw Error('Área de investimento inválida.');
    if(key==='stadium'){
      const capacity=Math.max(0,Number(t?.capacity)||0);let level=1;
      for(let i=1;i<STADIUM_CAPACITIES18374.length;i++){if(capacity<STADIUM_CAPACITIES18374[i])break;level=i+1;}
      return level;
    }
    const legacy=key==='training'||key==='youth'||key==='medical',raw=legacy?t?.[key+'Level']:t?.management18374?.levels?.[key];
    if(Number.isFinite(Number(raw)))return clamp(Math.trunc(Number(raw)),1,12);
    return 1;
  }
  function facilityStrength18374(t,key){const n=facilityLevel18374(t,key);return n<=5?n:5+(n-5)*.25;}
  function managementPlan18374(t){const key=t?.management18374?.plan;return Object.hasOwn(PLANS18374,key)?PLANS18374[key]:PLANS18374.balanced;}
  function managementDevelopment18374(t,p){
    const plan=t?.management18374?.plan;
    return plan==='development'?(Number(p?.age)<=23?1.10:.95):plan==='economy'?.92:1;
  }
  function managementRecovery18374(t){const plan=t?.management18374?.plan;return plan==='performance'?1.5:plan==='economy'?-1:0;}
  function management18374(t){
    if(!t||typeof t!=='object')throw Error('Clube indisponível.');
    let m=t.management18374;
    if(!m||typeof m!=='object')m=t.management18374={version:1,levels:{},projects:[],plan:'balanced',serial:0};
    if(!m.levels||typeof m.levels!=='object')m.levels={};
    if(!Array.isArray(m.projects))m.projects=[];
    if(!Object.hasOwn(PLANS18374,m.plan))m.plan='balanced';
    m.serial=Math.max(0,Math.trunc(Number(m.serial)||0));
    return m;
  }
  function managementGuard18374(s,clubId){
    if(!s||s.userEmployed===false)throw Error('Assuma um clube para gerenciar seus investimentos.');
    if(s.v640National?.userTeam)throw Error('Investimentos de clube não estão disponíveis para seleções.');
    if(s.live)throw Error('Conclua a partida antes de gerenciar o clube.');
    if(s.vacation?.active||s.v18373JobWaitPartial)throw Error('Pare a simulação antes de alterar a gestão.');
    const t=human(s);if(!t||clubId&&String(t.id)!==String(clubId))throw Error('O clube mudou. Abra novamente o investimento.');
    const me=s.coaches?.[s.userCoachId];if(me&&(String(me.clubId)!==String(t.id)||t.coachId&&String(t.coachId)!==String(s.userCoachId)))throw Error('Você não está mais no comando deste clube.');
    if(!Number.isFinite(t.balance))throw Error('O caixa do clube está indisponível. Reabra a carreira antes de investir.');
    return t;
  }
  function managementExtraUpkeep18374(t){
    let total=0;for(const key of ['scouting','analytics','commercial','supporters'])total+=(facilityLevel18374(t,key)-1)*MANAGEMENT18374[key].upkeep;
    return total;
  }
  function managementUpkeep18374(s,t){
    const fc=t.id===s.user?financialChallenge724(s):FINANCIAL_CHALLENGE724.normal,brand=Math.max(0,(t.base||50)-45);
    const amount=(Number(t.capacity)||0)*18+facilityLevel18374(t,'training')*100000+facilityLevel18374(t,'medical')*78000+facilityLevel18374(t,'youth')*68000+brand*18000+managementExtraUpkeep18374(t);
    return Math.round(amount*fc.operating*managementPlan18374(t).upkeep);
  }
  function managementScout18374(t,base={level:1,name:'Básico',target:12,accuracy:88}){
    const n=facilityLevel18374(t,'scouting'),gain=n-1;
    return {...base,target:Math.max(4,Math.round(Number(base.target)-gain*.45)),accuracy:Math.min(99,Number(base.accuracy)+gain*.5),name:base.name+(gain?' · rede '+n:''),facilityLevel:n};
  }
  function managementBenefit18374(t,key,level=facilityLevel18374(t,key)){
    const effective=level<=5?level:5+(level-5)*.25;
    if(key==='stadium')return Math.round(Number(t.capacity)||0).toLocaleString('pt-BR')+' lugares';
    if(key==='training')return 'Ritmo do treino +'+Math.round(((.17+effective*.075)/.245-1)*100)+'%';
    if(key==='youth')return 'Ritmo de formação +'+Math.round(((.28+effective*.10)/.38-1)*100)+'%; captação aprimorada';
    if(key==='medical')return '+'+(effective*1.2).toFixed(1).replace('.',',')+' de energia na recuperação';
    if(key==='scouting')return 'Prazo do olheiro até -'+((level-1)*.45).toFixed(1).replace('.',',')+' jornadas; precisão +'+((level-1)*.5).toFixed(1).replace('.',',')+' p.p.';
    if(key==='analytics')return 'Aprendizado por atuação +'+Math.round((level-1)*1.5)+'%';
    if(key==='commercial')return 'Patrocínio e comercial +'+Math.round((level-1)*2)+'%';
    return 'Demanda por ingressos +'+Math.round((level-1)*1.2)+'%';
  }
  function upgradeCost(t,type){
    if(!Object.hasOwn(MANAGEMENT18374,type))throw Error('Área de investimento inválida.');
    const level=facilityLevel18374(t,type);
    if(type==='stadium')return Math.round((1800000+(Number(t.capacity)||0)*43)*Math.pow(1.35,Math.max(0,level-4))/1000)*1000;
    return Math.round(MANAGEMENT18374[type].base*Math.pow(1.82,level-1)/1000)*1000;
  }
  function managementQuote18374(s,t,type){
    if(!Object.hasOwn(MANAGEMENT18374,type))throw Error('Área de investimento inválida.');const spec=MANAGEMENT18374[type];
    const level=facilityLevel18374(t,type),target=level+1,projects=Array.isArray(t.management18374?.projects)?t.management18374.projects:[],active=projects.find(p=>p?.type===type),max=level>=12;
    const duration=Math.ceil((4+target*2+Math.max(0,target-5)*3)*(type==='stadium'?1.35:1));
    const extraSeats=type==='stadium'?Math.max(0,(STADIUM_CAPACITIES18374[Math.min(11,target-1)]||0)-(Number(t.capacity)||0)):0;
    const fc=t.id===s.user?financialChallenge724(s):FINANCIAL_CHALLENGE724.normal;
    const extraMaintenance=Math.round((type==='stadium'?extraSeats*18:spec.upkeep)*fc.operating*managementPlan18374(t).upkeep);
    const cost=max?0:upgradeCost(t,type),reason=max?'Estrutura concluída':active?'Projeto em andamento':projects.length>=2?'Duas obras em andamento':!Number.isFinite(t.balance)||t.balance<cost?'Caixa insuficiente':'';
    return {type,name:spec.name,icon:spec.icon,level,target,max,cost,duration,extraSeats,extraMaintenance,active:active||null,reason,
      currentBenefit:managementBenefit18374(t,type),nextBenefit:type==='stadium'?(Number(t.capacity)+extraSeats).toLocaleString('pt-BR')+' lugares':managementBenefit18374(t,type,target)};
  }
  function upgrade(s,type,clubId){
    const t=managementGuard18374(s,clubId),quote=managementQuote18374(s,t,type);
    if(quote.reason)throw Error(quote.reason+'.');
    const m=management18374(t),id=String(t.id)+'-obra-'+(++m.serial)+'-'+s.year+'-'+s.day;
    const project={id,type,from:quote.level,target:quote.target,cost:quote.cost,total:quote.duration,remaining:quote.duration,seats:quote.extraSeats,startedYear:s.year,startedDay:s.day};
    ledger(s,t,'Projeto de estrutura',-quote.cost,quote.name+' · nível '+quote.target);
    m.projects.push(project);
    news(s,'Novo projeto no clube',t.name+' iniciou '+quote.name.toLowerCase()+'. Prazo: '+quote.duration+' jornadas.','info');
    return quote.cost;
  }
  function cancelProject18374(s,id,clubId){
    const t=managementGuard18374(s,clubId),m=management18374(t),index=m.projects.findIndex(p=>p?.id===id);
    if(index<0)throw Error('Este projeto já terminou ou foi cancelado.');
    const p=m.projects[index];if(!Object.hasOwn(MANAGEMENT18374,p.type)||!Number.isFinite(p.cost)||!Number.isFinite(p.remaining)||!Number.isFinite(p.total))throw Error('Os dados do projeto estão indisponíveis.');
    const refund=Math.floor(p.cost*clamp(p.remaining/Math.max(1,p.total),0,1)*.85);
    m.projects.splice(index,1);if(refund)ledger(s,t,'Cancelamento de projeto',refund,MANAGEMENT18374[p.type].name+' · devolução da parte não executada');
    news(s,'Projeto cancelado',t.name+' cancelou '+MANAGEMENT18374[p.type].name.toLowerCase()+'. A estrutura concluída foi mantida.','info');
    return refund;
  }
  function setManagementPlan18374(s,plan,clubId){
    if(!Object.hasOwn(PLANS18374,plan))throw Error('Plano de gestão inválido.');
    const t=managementGuard18374(s,clubId);management18374(t).plan=plan;return plan;
  }
  function tickManagement18374(s,t){
    const m=t.management18374;if(!m||!Array.isArray(m.projects)||!m.projects.length)return 0;
    const stamp=String(s.year)+':'+String(s.day);if(m.lastTick===stamp)return 0;m.lastTick=stamp;
    let completed=0;for(let i=m.projects.length-1;i>=0;i--){
      const p=m.projects[i];if(!p||!Object.hasOwn(MANAGEMENT18374,p.type)||!Number.isFinite(p.remaining)||p.remaining<=0||!Number.isInteger(p.target)||p.target<2||p.target>12)continue;
      p.remaining--;if(p.remaining>0)continue;
      const current=facilityLevel18374(t,p.type);if(current===p.from){
        if(['training','youth','medical'].includes(p.type))t[p.type+'Level']=p.target;else m.levels[p.type]=p.target;
        if(p.type==='stadium')t.capacity=Math.max(Number(t.capacity)||0,Math.min(120000,(Number(t.capacity)||0)+(Number(p.seats)||0)));
        completed++;if(t.id===s.user&&s.userEmployed!==false)news(s,'Estrutura pronta',MANAGEMENT18374[p.type].name+' do '+t.name+' chegou ao nível '+p.target+'. Os benefícios já estão ativos.','good');
      }
      m.projects.splice(i,1);
    }return completed;
  }
  /* FUTBR_CLUB_MANAGEMENT_18374_END */
'''

UI = r'''
/* FUTBR_CLUB_MANAGEMENT_UI_18374 */
function v18374ManagementBlocked(){return !!(state?.live||state?.vacation?.active||state?.userEmployed===false||v53Sim?.active||v53Sim?.starting||v53Sim?.syncing||v52Processing);}
function v18374ManagementRow(t,key){
 const q=E.managementQuote18374(state,t,key),p=q.active,disabled=v18374ManagementBlocked(),remaining=p?Math.max(0,p.remaining):0;
 return `<article class="v18374-facility" data-facility="${key}"><div class="v18374-facility-head"><span class="v18374-facility-icon">${icon(q.icon,19)}</span><div><h3>${esc(q.name)}</h3><span class="tiny muted">Nível <b>${q.level}</b> / 12</span></div><span class="v18374-level-tier">${q.level<=3?'LOCAL':q.level<=6?'REGIONAL':q.level<=9?'NACIONAL':'REFERÊNCIA'}</span></div><div class="v18374-levels" aria-label="Nível ${q.level} de 12">${Array.from({length:12},(_,i)=>`<span class="${i<q.level?'on':''}"></span>`).join('')}</div><p class="v18374-benefit">${esc(q.currentBenefit)}</p>${p?`<div class="v18374-project"><div class="flex between"><strong>Nível ${p.target} em construção</strong><span>${remaining} jornada${remaining===1?'':'s'}</span></div><progress max="${p.total}" value="${p.total-remaining}" aria-label="Progresso do projeto"></progress><div class="flex between"><small>${compact(p.cost)} já investidos</small>${button('v18374-cancel-project','Cancelar','small ghost',`data-project="${esc(p.id)}" data-team="${esc(t.id)}" ${disabled?'disabled':''}`)}</div></div>`:q.max?'<div class="v18374-next"><strong>Estrutura concluída</strong><small>O clube mantém todos os benefícios deste nível.</small></div>':`<div class="v18374-next"><small>PRÓXIMO NÍVEL</small><span>${esc(q.nextBenefit)}</span><div class="v18374-project-terms"><span>${icon('clock',12)} ${q.duration} jornadas</span><span>Manutenção +${compact(q.extraMaintenance)}/j.</span></div>${button('upgrade',`${compact(q.cost)} · Planejar`,'small secondary',`data-upgrade="${key}" ${disabled||q.reason?'disabled':''}`)}${q.reason?`<small class="gold">${esc(q.reason)}</small>`:''}</div>`}</article>`;
}
clubPage=function(){
 const t=state&&E.human(state),me=state?.coaches?.[state?.userCoachId];
 if(!state||!t||state.userEmployed===false||state.v640National?.userTeam||me&&(String(me.clubId)!==String(t.id)||t.coachId&&String(t.coachId)!==String(state.userCoachId)))return `<section class="panel"><div class="panel-body"><h2>Gestão do clube</h2><p>Assuma um clube para planejar investimentos e acompanhar sua estrutura.</p></div></section>`;
 const m=t.management18374||{plan:'balanced',projects:[]},pay=E.payroll(state,t),day=Math.max(0,state.day-1),last=(t.ledger||[]).filter(l=>l.year===state.year&&l.day===day),income=E.sum(last.filter(l=>l.amount>0).map(l=>l.amount)),expense=E.sum(last.filter(l=>l.amount<0).map(l=>-l.amount)),locked=v18374ManagementBlocked(),plans=E.managementPlans18374,plan=Object.hasOwn(plans,m.plan)?plans[m.plan]:plans.balanced,projects=Array.isArray(m.projects)?m.projects:[],upkeep=E.managementUpkeep18374(state,t),ledger=(t.ledger||[]).slice(0,160);
 const vacation=state.v93LastVacationFinance;
 return `<div class="v18374-club-page"><header class="v18374-club-header"><div class="flex gap12">${badge(t,'small')}<div><span class="eyebrow">CONSTRUA O FUTURO</span><h1>Clube &amp; Finanças</h1><p>${esc(t.name)}</p></div></div><button type="button" class="btn small ghost" data-v51-action="palette" data-team="${esc(t.id)}">Ajustar cores</button></header><div class="v18374-finance-strip"><div><small>Caixa disponível</small><strong class="${t.balance<0?'red':'green'}">${compact(t.balance)}</strong></div><div><small>Folha por jornada</small><strong>${compact(pay)}</strong></div><div><small>Manutenção por jornada</small><strong>${compact(upkeep)}</strong></div><div><small>Última jornada</small><strong class="${income-expense<0?'red':'green'}">${income-expense>0?'+':''}${compact(income-expense)}</strong></div></div>${t.balance<0?'<div class="notice">Caixa negativo: avalie os custos antes de iniciar novos projetos.</div>':''}<div class="v18374-club-scroll"><div class="v18374-management-layout"><aside class="panel v18374-plan"><div class="panel-head"><h3>Plano do clube</h3>${icon('flag',16)}</div><div class="panel-body"><div class="field"><label for="v18374-plan">Prioridade da gestão</label><select id="v18374-plan" data-management18374="plan" data-team="${esc(t.id)}" ${locked?'disabled':''}>${options(Object.fromEntries(Object.entries(plans).map(([k,v])=>[k,v.name])),m.plan||'balanced')}</select><p class="subtext v18374-plan-description">${esc(plan.description)}</p></div><div class="v18374-plan-fields"><div class="field"><label for="ticket-price">Ingresso (R$)</label><input id="ticket-price" type="number" min="10" max="150" step="1" data-club="ticket" value="${t.ticket}" ${locked?'disabled':''}><small>O preço influencia a ocupação do estádio.</small></div><div class="field"><label for="sponsor-choice">Patrocinador</label><select id="sponsor-choice" data-club="sponsor" ${locked?'disabled':''}>${options(LABEL.sponsor,t.sponsor)}</select></div></div><div class="v18374-construction-summary"><strong>${projects.length} / 2 projetos em andamento</strong><p>Os benefícios começam na conclusão. Obras continuam entre temporadas e pertencem ao clube.</p><p>Níveis avançados exigem mais investimento e tempo. Até duas obras simultâneas.</p></div>${vacation&&Number(vacation.year)===Number(state.year)?`<p class="subtext">Saldo das últimas férias: <b>${compact(vacation.delta)}</b></p>`:''}<details class="v18374-ledger"><summary>Movimentação financeira <span>${ledger.length} lançamentos</span></summary><div class="v18374-ledger-scroll">${ledger.length?`<table><thead><tr><th>Jornada</th><th>Descrição</th><th class="number">Valor</th></tr></thead><tbody>${ledger.map(l=>`<tr><td>${l.year} · ${l.day+1}</td><td><b>${esc(l.category)}</b><small>${esc(l.note)}</small></td><td class="number ${l.amount<0?'red':'green'}">${l.amount>0?'+':''}${cash(l.amount)}</td></tr>`).join('')}</tbody></table>`:'<p class="empty">Sem lançamentos.</p>'}</div></details></div></aside><section class="v18374-investments"><div class="v18374-investment-heading"><div><h2>Estrutura e desenvolvimento</h2><p>Oito áreas para desenvolver ao longo da sua passagem.</p></div><span class="pill">ATÉ 12 NÍVEIS</span></div><div class="v18374-facilities">${Object.keys(E.managementAreas18374).map(key=>v18374ManagementRow(t,key)).join('')}</div></section></div></div></div>`;
};
showUpgrade=function(type){
 guardManage();if(v18374ManagementBlocked())throw Error('Aguarde o fim da simulação para investir.');
 const t=E.human(state),q=E.managementQuote18374(state,t,type);if(q.reason)throw Error(q.reason+'.');
 modal(modalHead('Planejar investimento',q.name+' · nível '+q.level+' → '+q.target)+`<div class="modal-body v18374-invest-modal"><p>${esc(q.nextBenefit)}</p><div class="v18374-quote-grid"><div><small>Investimento agora</small><strong>${cash(q.cost)}</strong></div><div><small>Prazo de execução</small><strong>${q.duration} jornadas</strong></div><div><small>Manutenção após concluir</small><strong>+ ${cash(q.extraMaintenance)} / jornada</strong></div><div><small>Caixa após investir</small><strong>${cash(t.balance-q.cost)}</strong></div></div><p class="subtext">O valor é pago no início. A melhoria entra em funcionamento ao concluir o projeto. Se cancelar antes, recebe 85% do valor proporcional à parte ainda não executada.</p><p class="subtext mt12">A obra continua na próxima temporada. O clube pode manter até dois projetos em andamento.</p></div><div class="modal-footer">${button('close','Voltar','secondary')}${button('v18374-start-project','Iniciar projeto','primary',`data-upgrade="${esc(type)}" data-team="${esc(t.id)}"`)}</div>`,'club-investment-18374');
};
function v18374CancelProjectModal(id,teamId){
 guardManage();const t=E.human(state);if(String(t.id)!==String(teamId))throw Error('O clube mudou.');
 const p=t.management18374?.projects?.find(x=>x.id===id);if(!p)throw Error('O projeto não está mais em andamento.');
 const refund=Math.floor(p.cost*p.remaining/p.total*.85),title=E.managementAreas18374[p.type].name;
 modal(modalHead('Cancelar projeto',title)+`<div class="modal-body"><p>O projeto será encerrado. O nível atual da estrutura será mantido.</p><div class="cost-summary"><span>Devolução para o caixa</span><strong>${cash(refund)}</strong></div><p class="subtext">São devolvidos 85% do valor proporcional às ${p.remaining} jornadas que ainda faltam. O valor executado e a taxa de cancelamento não são reembolsados.</p></div><div class="modal-footer">${button('close','Manter projeto','secondary')}${button('v18374-confirm-cancel','Cancelar projeto','danger',`data-project="${esc(id)}" data-team="${esc(teamId)}"`)}</div>`,'club-cancel-18374');
}
const v18374ManagementBaseAct=act;
act=function(el){
 const a=el?.dataset?.action;
 if(a==='v18374-start-project'||a==='v18374-confirm-cancel'||a==='v18374-cancel-project'){
  guardManage();if(v18374ManagementBlocked())throw Error('Aguarde o fim da simulação para alterar os projetos.');
  if(a==='v18374-cancel-project'){v18374CancelProjectModal(el.dataset.project,el.dataset.team);return;}
  if(a==='v18374-start-project')E.upgrade(state,el.dataset.upgrade,el.dataset.team);
  else E.cancelProject18374(state,el.dataset.project,el.dataset.team);
  persist();closeModal();render();toast(a==='v18374-start-project'?'Projeto iniciado. Acompanhe a execução em Clube & Finanças.':'Projeto cancelado. A devolução entrou no caixa.','success');return;
 }
 return v18374ManagementBaseAct(el);
};
document.addEventListener('change',event=>{
 const el=event.target;if(!el?.dataset?.management18374)return;
 event.preventDefault();event.stopImmediatePropagation();
 try{guardManage();if(v18374ManagementBlocked())throw Error('Aguarde o fim da simulação para alterar o plano.');E.setManagementPlan18374(state,el.value,el.dataset.team);persist();render();toast('Plano do clube atualizado.','success');}
 catch(error){toast(error?.message||'Não foi possível alterar o plano.','warn');render();}
},true);
const v18374ScoutDepartment=v638Department;
v638Department=function(){const base=v18374ScoutDepartment(),t=state&&E.human(state);return t?E.managementScout18374(t,base):base;};
const v18374ManagementStyle=document.createElement('style');v18374ManagementStyle.id='futbr-club-management-18374';v18374ManagementStyle.textContent=`
body.v570-club-finance-view #v555-page{display:block!important;overflow:hidden!important}
.v18374-club-page{height:100%;min-height:0;display:flex;flex-direction:column;gap:14px;color:var(--text)}
.v18374-club-header{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-shrink:0;padding:2px 0}.v18374-club-header h1{font-size:25px;margin:4px 0;line-height:1.1}.v18374-club-header p{font-size:12px;color:var(--muted)}.v18374-club-header .shield{width:42px;height:47px}
.v18374-finance-strip{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;flex-shrink:0}.v18374-finance-strip>div{border:1px solid var(--line);background:var(--panel);border-radius:11px;padding:13px 15px}.v18374-finance-strip small{display:block;color:var(--muted);font-size:10px;margin-bottom:7px}.v18374-finance-strip strong{font-size:23px;white-space:nowrap}
.v18374-club-scroll{flex:1;min-height:0;overflow:auto;overscroll-behavior:contain;padding-right:6px;padding-bottom:14px;scrollbar-gutter:stable}.v18374-management-layout{display:grid;grid-template-columns:minmax(260px,.65fr) minmax(530px,1.55fr);gap:16px;align-items:start}.v18374-plan .panel-head,.v18374-plan .panel-body{padding:16px}.v18374-plan .field{margin-bottom:15px}.v18374-plan .field select,.v18374-plan .field input{width:100%;min-height:39px}.v18374-plan .field small{font-size:10px;color:var(--muted);line-height:1.5}.v18374-plan-description{line-height:1.65;min-height:48px;margin-top:8px}.v18374-plan-fields{display:grid;gap:12px;grid-template-columns:1fr 1fr}.v18374-construction-summary{padding:13px;background:var(--club-soft,#ffffff08);border:1px solid var(--line);border-radius:9px}.v18374-construction-summary strong{font-size:12px}.v18374-construction-summary p{font-size:10px;line-height:1.65;color:var(--muted);margin-top:8px}
.v18374-investment-heading{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:12px}.v18374-investment-heading h2{font-size:17px;margin-bottom:5px}.v18374-investment-heading p{font-size:11px;color:var(--muted)}.v18374-facilities{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.v18374-facility{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:15px;min-width:0}.v18374-facility-head{display:flex;align-items:center;gap:9px}.v18374-facility-head h3{font-size:12px;margin-bottom:5px;line-height:1.3}.v18374-facility-icon{width:33px;height:37px;flex:0 0 33px;display:grid;place-items:center;color:var(--accent);border-radius:8px;background:var(--club-soft,#ffffff08)}.v18374-level-tier{margin-left:auto;font-size:8px;color:var(--dim);letter-spacing:.5px}.v18374-levels{display:flex;gap:3px;margin:13px 0 10px}.v18374-levels span{height:5px;flex:1;border-radius:3px;background:var(--line)}.v18374-levels .on{background:var(--accent)}.v18374-benefit{font-size:11px;color:var(--text);line-height:1.5;min-height:32px}.v18374-next{display:flex;flex-direction:column;gap:7px;padding-top:10px;margin-top:10px;border-top:1px solid var(--line)}.v18374-next>small{font-size:9px;color:var(--muted)}.v18374-next>span{font-size:11px;line-height:1.4}.v18374-next .btn{width:100%;margin-top:4px;min-height:34px}.v18374-project-terms{display:flex;justify-content:space-between;gap:7px;font-size:9px;color:var(--muted);flex-wrap:wrap}.v18374-project-terms span{display:flex;align-items:center;gap:4px}.v18374-project{border-top:1px solid var(--line);padding-top:12px;margin-top:10px;font-size:10px}.v18374-project strong{font-size:11px;color:var(--accent)}.v18374-project progress{width:100%;height:7px;accent-color:var(--accent);margin:12px 0}.v18374-project small{color:var(--muted);font-size:9px}
.v18374-ledger{margin-top:18px;border-top:1px solid var(--line);padding-top:12px}.v18374-ledger summary{font-size:12px;font-weight:600;cursor:pointer}.v18374-ledger summary span{display:block;font-size:10px;font-weight:400;color:var(--muted);margin-top:5px}.v18374-ledger-scroll{max-height:320px;overflow:auto;margin-top:12px}.v18374-ledger table{font-size:10px}.v18374-ledger th{position:sticky;top:0;background:var(--panel);font-size:8px}.v18374-ledger td,.v18374-ledger th{padding:8px 5px}.v18374-ledger td small{display:block;font-size:9px;color:var(--muted);margin-top:4px;line-height:1.4}
.v18374-quote-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:18px 0}.v18374-quote-grid>div{background:var(--club-soft,#ffffff08);border:1px solid var(--line);border-radius:9px;padding:13px}.v18374-quote-grid small{display:block;color:var(--muted);font-size:10px;margin-bottom:7px}.v18374-quote-grid strong{font-size:16px}.v18374-invest-modal>p{line-height:1.65}
@media(max-width:1200px){.v18374-management-layout{grid-template-columns:minmax(230px,.62fr) minmax(420px,1.38fr)}.v18374-facility{padding:11px}.v18374-level-tier{display:none}.v18374-plan-fields{grid-template-columns:1fr}.v18374-finance-strip strong{font-size:19px}}
@media(max-width:900px){body.v570-club-finance-view #v555-page{overflow:visible!important}.v18374-club-page{height:auto}.v18374-management-layout{grid-template-columns:1fr}.v18374-club-scroll{overflow:visible;padding:0}.v18374-plan-fields{grid-template-columns:1fr 1fr}.v18374-finance-strip{grid-template-columns:repeat(2,minmax(0,1fr))}.v18374-club-header h1{font-size:22px}.v18374-club-header .eyebrow{font-size:8px}}
@media(max-width:550px){.v18374-facilities{grid-template-columns:1fr}.v18374-club-header>.btn{font-size:9px;padding:6px}.v18374-quote-grid{grid-template-columns:1fr}.v18374-investment-heading{align-items:flex-start}.v18374-investment-heading .pill{font-size:8px;white-space:nowrap}}
`;
document.head.appendChild(v18374ManagementStyle);
window.GestorFC.management18374={version:'18.374.0',areas:8,maxLevel:12,maxProjects:2,clubOwnedProjects:true,render:()=>clubPage()};
/* FUTBR_CLUB_MANAGEMENT_UI_18374_END */
'''


def once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise RuntimeError(f'Expected one management anchor ({source.count(old)}): {old[:130]}')
    return source.replace(old, new, 1)


def install(source: str) -> str:
    if MARKER in source:
        return source
    start=source.index('  function upgradeCost(t,type){')
    end=source.index('  function promoteYouth(s,pos){',start)
    source=source[:start]+ENGINE+source[end:]
    source=once(source,'managerSettings18371,applyManagerSettings18371,',
        'managementAreas18374:MANAGEMENT18374,managementPlans18374:PLANS18374,management18374,facilityLevel18374,facilityStrength18374,managementDevelopment18374,managementRecovery18374,managementUpkeep18374,managementScout18374,managementQuote18374,cancelProject18374,setManagementPlan18374,tickManagement18374,managerSettings18371,applyManagerSettings18371,')
    source=once(source,'  function stageFinances(s,t,played){\n',
        "  function stageFinances(s,t,played){\n    const managementStamp18374=String(s.year)+':'+String(s.day);if(t.v18374FinanceStamp===managementStamp18374)return;\n    tickManagement18374(s,t);\n")
    source=once(source,'  function trainAndRecover(s,t,played){\n',
        '  function trainAndRecover(s,t,played){\n    tickManagement18374(s,t); // Also advances on national/world dates without a finance pass.\n')
    source=once(source,"sponsor=commercial*sponsorMode;", "sponsor=commercial*sponsorMode*(1+(facilityLevel18374(t,'commercial')-1)*.02);")
    source=once(source,'    const upkeep=(t.capacity*18+t.trainingLevel*100000+t.medicalLevel*78000+t.youthLevel*68000+Math.max(0,brand)*18000)*fc.operating;',
        '    const upkeep=managementUpkeep18374(s,t);')
    source=once(source,"'Saldo negativo: '+(fc.interest*100).toFixed(2).replace('.',',')+'% por jornada');\n  }",
        "'Saldo negativo: '+(fc.interest*100).toFixed(2).replace('.',',')+'% por jornada');t.v18374FinanceStamp=managementStamp18374;\n  }")
    # Keep the existing 1-5 effects; levels 6-12 have diminishing returns.
    engine_end=source.index("if(typeof module!=='undefined'&&module.exports)module.exports=Engine;")
    engine,ui=source[:engine_end],source[engine_end:]
    for old,new in [
        ('appeal*priceFactor,.12,.98',"appeal*priceFactor*(1+(facilityLevel18374(t,'supporters')-1)*.012),.12,.98"),
        ('t.trainingLevel*.075',"facilityStrength18374(t,'training')*.075"),
        ('t.trainingLevel*.032',"facilityStrength18374(t,'training')*.032"),
        ('(t.trainingLevel-1)*.055',"(facilityStrength18374(t,'training')-1)*.055"),
        ('t.medicalLevel*1.2',"facilityStrength18374(t,'medical')*1.2+managementRecovery18374(t)"),
        ('t.medicalLevel*1.7',"facilityStrength18374(t,'medical')*1.7+managementRecovery18374(t)"),
        ('clamp(Number(t.youthLevel)||1,1,5)',"facilityStrength18374(t,'youth')"),
        ('*v18123DevelopmentRate(t,p)',"*v18123DevelopmentRate(t,p)*managementDevelopment18374(t,p)"),
        ("quality*minutes*age*training*academyGraduate", "quality*minutes*age*training*academyGraduate*(1+(facilityLevel18374(t,'analytics')-1)*.015)"),
        ("*(t.academyPlan==='intensive'?1.20:1);", "*(t.academyPlan==='intensive'?1.20:1)*managementDevelopment18374(t,p);")
    ]:
        if old not in engine: raise RuntimeError('Missing engine benefit anchor: '+old)
        engine=engine.replace(old,new)
    for old,new in [
        ('E.clamp(Number(t?.youthLevel)||1,1,5)',"E.facilityStrength18374(t,'youth')"),
        ('(Number(t.youthLevel)||1)*.10',"E.facilityStrength18374(t,'youth')*.10"),
        ('Math.max(0,(Number(t.trainingLevel)||1)-1)*2',"Math.max(0,E.facilityStrength18374(t,'training')-1)*2"),
        ('Math.max(0,(Number(t.youthLevel)||1)-1)*1.5',"Math.max(0,E.facilityStrength18374(t,'youth')-1)*1.5"),
        ("*(t.academyPlan==='intensive'?1.20:1);", "*(t.academyPlan==='intensive'?1.20:1)*E.managementDevelopment18374(t,p);"),
        ('medical=Number(t.medicalLevel)||1;',"medical=E.facilityStrength18374(t,'medical');")
    ]:
        if old not in ui: raise RuntimeError('Missing UI benefit anchor: '+old)
        ui=ui.replace(old,new)
    source=engine+ui
    # The final in-scope insertion is after every earlier club renderer and after
    # the partial-world guards, but before the IIFE closes. Workers receive Engine.
    anchor='window.GestorFC.render=render;\n\n})();\n</script>\n\n\n\n\n<!-- v43 clean: v130 ranking warmup removed -->'
    source=once(source,anchor,'window.GestorFC.render=render;\n'+UI+'\n})();\n</script>\n\n\n\n\n<!-- v43 clean: v130 ranking warmup removed -->')
    source=source.replace("toast('Investimento concluído.');return;}","toast('Projeto iniciado. Acompanhe a execução em Clube & Finanças.');return;}",1)
    return source


def main():
    if len(sys.argv)!=2: raise SystemExit('usage: expand_club_management_18374.py <project>')
    root=Path(sys.argv[1]).resolve();path=root/'src/index.html'
    source=install(path.read_text(encoding='utf-8'))
    path.write_text(source,encoding='utf-8')
    report={'ok':True,'version':'18.374.0','areas':8,'maxLevel':12,'maxConcurrentProjects':2,
        'projectsBelongToClubs':True,'constructionInExistingDailyPasses':True,'legacyLevelsPreserved':True,
        'realBoundedBenefits':True,'noAdditionalWorldPlayerLoop':True,'inGameProjectConfirmations':True,
        'sourceSha256':hashlib.sha256(source.encode('utf-8')).hexdigest()}
    (root/'club-management-18374-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__': main()
