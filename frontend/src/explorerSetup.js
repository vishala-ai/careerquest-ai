// Creation receipts survive a lost response and a browser reload. They do not
// select an explorer; only a validated backend profile response can do that.
export function setupProblems({nickname='',grade='',fictional=false}) {
  const issues=[];
  if(nickname.trim().length<2||nickname.trim().length>40)issues.push('Enter an explorer nickname (2–40 characters).');
  if(![9,10,11,12].includes(Number(grade)))issues.push('Choose Grade 9, 10, 11 or 12.');
  if(!fictional)issues.push('Confirm that you will use aliases and test data only.');
  return issues;
}
export function creationRequest(values, storage=sessionStorage, newKey=()=>crypto.randomUUID()) {
  const issues=setupProblems(values);if(issues.length)throw Error(issues.join(' '));
  const body={alias:values.nickname.trim(),grade:Number(values.grade),fictional_ack:true};
  let previous;try{previous=JSON.parse(storage.getItem('cq_pending_creation')||'null');}catch{}
  const creation_key=previous?.payload===JSON.stringify(body)&&typeof previous.key==='string'?previous.key:newKey();
  storage.setItem('cq_pending_creation',JSON.stringify({payload:JSON.stringify(body),key:creation_key}));
  return {...body,creation_key};
}
export function finishCreation(storage=sessionStorage){storage.removeItem('cq_pending_creation');}
export async function availableExplorers(remembered, getProfile) {
  // Only validate IDs already associated with this browser. Never query a global list.
  const saved=await Promise.all(remembered.map(async item=>{
    try{const result=await getProfile(item.id);return {...item,alias:result.profile.alias,grade:result.profile.grade};}
    catch(error){if(error.status===404)return null;throw error;}
  }));
  return saved.filter(Boolean);
}

// Explicitly leave the active journey; remembered explorers and receipts stay intact.
export function leaveExplorer(storage=localStorage){storage.removeItem('cq_pid');}
