// Unsaved input transaction only. This never stores progress, XP or confirmation.
export const emptyDiscoveryEditor={editing:false,draft:''};
export function discoveryEditor(editor,action) {
  if(action.type==='edit')return {editing:true,draft:action.choice};
  if(action.type==='choose')return {...editor,draft:action.choice};
  if(action.type==='cancel'||action.type==='reset')return emptyDiscoveryEditor;
  return editor;
}
