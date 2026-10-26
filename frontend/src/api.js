let csrfToken='';
export function setCsrfToken(value){csrfToken=value||'';}
export async function api(path, method = 'GET', body) {
  const response = await fetch(`/api${path}`, {method, credentials:'same-origin', headers: {'Content-Type': 'application/json','X-CQ-Request':'1',...(method!=='GET'?{'X-CSRF-Token':csrfToken}:{})}, body: body === undefined ? undefined : JSON.stringify(body)});
  let data;
  try{data=await response.json();}catch{
    const error=new Error('The service is unavailable. Please try again.');error.status=response.status;throw error;
  }
  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map(item => item.msg).join('. ') : data.detail;
    const error = new Error(detail || 'Something went wrong. Please try again.');
    error.status = response.status;
    if(response.status===401&&!path.startsWith('/auth/'))window.dispatchEvent(new Event('cq-session-expired'));
    throw error;
  }
  return data;
}
