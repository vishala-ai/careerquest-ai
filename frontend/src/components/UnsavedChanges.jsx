import React,{useEffect,useRef} from 'react';
import {Button} from './Shared';
export default function UnsavedChanges({profileDirty,busy,error,onStay,onDiscard,onSave,description}) {
  const dialog=useRef(null);
  useEffect(()=>{dialog.current.showModal();},[]);
  return <dialog ref={dialog} className="unsaved-dialog" aria-labelledby="unsaved-title" onCancel={event=>{event.preventDefault();onStay();}}><span className="eyebrow">YOUR CHOICES MATTER</span><h2 id="unsaved-title">Keep your changes?</h2><p>{description||(profileDirty?'Your profile has unsaved edits. Save them as an unconfirmed draft before leaving, or stay here to finish reviewing.':'Your quest answer has unsaved changes. Keep editing to save it, or explicitly leave without saving.')}</p>{error&&<p className="error alert" role="alert">{error}</p>}<div className="button-row"><Button autoFocus className="secondary" disabled={busy} onClick={onStay}>Keep editing</Button>{profileDirty&&<Button busy={busy} onClick={onSave}>Save draft & leave</Button>}<Button className="ghost" disabled={busy} onClick={onDiscard}>Leave without saving</Button></div></dialog>;
}
