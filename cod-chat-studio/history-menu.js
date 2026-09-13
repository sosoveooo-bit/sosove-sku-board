(function(root){
  'use strict';
  function create({getSession,available,change,status}){
    document.body.insertAdjacentHTML('beforeend',`
      <div id="historyMenu" class="history-menu" role="menu" aria-label="对话操作" hidden>
        <button role="menuitem" data-history-action="rename"><span aria-hidden="true">✎</span>重命名</button>
        <button role="menuitem" data-history-action="favorite"><span aria-hidden="true">☆</span><span id="favoriteLabel">收藏</span></button>
        <div class="menu-divider" role="separator"></div>
        <button role="menuitem" data-history-action="delete" class="danger"><span aria-hidden="true">⌫</span>删除</button>
      </div>
      <dialog id="historyDialog" aria-labelledby="historyDialogTitle" aria-describedby="historyDialogDescription">
        <form id="historyActionForm">
          <h2 id="historyDialogTitle"></h2><p id="historyDialogDescription"></p>
          <label id="historyNameLabel">对话名称<input id="historyName" maxlength="80" autocomplete="off"></label>
          <p id="historyDialogError" role="alert"></p>
          <div class="history-dialog-actions"><button type="button" id="historyCancel">取消</button><button type="submit" id="historyConfirm">保存</button></div>
        </form>
      </dialog>`);
    const menu=document.querySelector('#historyMenu'),dialog=document.querySelector('#historyDialog');
    const input=document.querySelector('#historyName'),confirm=document.querySelector('#historyConfirm');
    const cancel=document.querySelector('#historyCancel'),error=document.querySelector('#historyDialogError');
    let targetId=null,anchor=null,dialogAction=null,saving=false;
    function focusAnchor(){if(anchor?.isConnected)anchor.focus({preventScroll:true});}
    function close(restore=false){menu.hidden=true;if(restore)focusAnchor();}
    function open(id,x,y,source){
      const session=getSession(id);if(!available()||!session)return;
      targetId=id;anchor=source;
      document.querySelector('#favoriteLabel').textContent=session.favorite?'取消收藏':'收藏';
      menu.hidden=false;
      menu.style.left=Math.max(8,Math.min(x,innerWidth-menu.offsetWidth-8))+'px';
      menu.style.top=Math.max(8,Math.min(y,innerHeight-menu.offsetHeight-8))+'px';
      menu.querySelector('button').focus({preventScroll:true});
    }
    function showDialog(action,id){
      const session=getSession(id);if(!available()||!session)return;
      dialogAction={action,id};error.textContent='';
      const rename=action==='rename';
      document.querySelector('#historyDialogTitle').textContent=rename?'重命名对话':'删除这条对话？';
      const pending=Object.values(session.jobs||{}).some(j=>!['完成','失败'].includes(j.state));
      document.querySelector('#historyDialogDescription').textContent=rename?'修改标题不会改变产品需求、提示词或生成结果。':
        `将删除「${session.title}」在当前浏览器中的对话、参考图和任务索引，删除后此处没有恢复入口。后台图片文件保留。${pending?'这条对话还有待处理任务，删除不会停止后台任务，建议先同步并保存结果。':''}`;
      document.querySelector('#historyNameLabel').hidden=!rename;input.disabled=!rename;input.required=rename;
      input.value=rename?session.title:'';input.setCustomValidity('');
      confirm.textContent=rename?'保存名称':'确认删除';confirm.classList.toggle('danger',!rename);
      dialog.showModal();if(rename){input.focus();input.select();}else cancel.focus();
    }
    menu.addEventListener('click',async event=>{
      const button=event.target.closest('[data-history-action]');if(!button)return;
      const id=targetId,action=button.dataset.historyAction;close();
      if(action!=='favorite'){showDialog(action,id);return;}
      try{await change(action,id);}catch(e){status(e.message);}finally{focusAnchor();}
    });
    document.addEventListener('contextmenu',event=>{
      const row=event.target.closest('[data-history-id]');if(!row)return;
      event.preventDefault();open(row.dataset.historyId,event.clientX,event.clientY,row.querySelector('.history-more'));
    });
    document.addEventListener('click',event=>{
      const button=event.target.closest('[data-history-menu]');
      if(button){const rect=button.getBoundingClientRect();open(button.dataset.historyMenu,rect.right,rect.bottom+4,button);return;}
      if(!menu.contains(event.target))close();
    });
    document.addEventListener('keydown',event=>{
      const row=event.target.closest?.('[data-history-id]');
      if(row&&(event.key==='ContextMenu'||(event.shiftKey&&event.key==='F10'))){
        event.preventDefault();const rect=row.getBoundingClientRect();open(row.dataset.historyId,rect.right,rect.bottom,row.querySelector('.history-more'));return;
      }
      if(menu.hidden)return;
      if(event.key==='Escape'){event.preventDefault();close(true);}
      if(event.key==='Tab'){close();return;}
      if(['ArrowDown','ArrowUp','Home','End'].includes(event.key)){
        event.preventDefault();const buttons=[...menu.querySelectorAll('button')],index=buttons.indexOf(document.activeElement);
        const next=event.key==='Home'?0:event.key==='End'?buttons.length-1:(index+(event.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length;buttons[next].focus({preventScroll:true});
      }
    });
    window.addEventListener('resize',()=>close());
    document.addEventListener('scroll',()=>close(),true);
    cancel.onclick=()=>{if(!saving)dialog.close();};
    dialog.addEventListener('cancel',event=>{if(saving)event.preventDefault();});
    dialog.addEventListener('close',focusAnchor);
    input.addEventListener('input',()=>input.setCustomValidity(''));
    document.querySelector('#historyActionForm').onsubmit=async event=>{
      event.preventDefault();if(saving||!dialogAction)return;
      if(dialogAction.action==='rename'&&!input.value.trim()){input.setCustomValidity('请输入对话名称');input.reportValidity();return;}
      saving=true;confirm.disabled=true;cancel.disabled=true;error.textContent='';
      try{await change(dialogAction.action,dialogAction.id,input.value);dialog.close();}
      catch(e){error.textContent=e.message;}
      finally{saving=false;confirm.disabled=false;cancel.disabled=false;}
    };
    return {close};
  }
  root.StudioHistory={create};
})(window);
