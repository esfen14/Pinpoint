import type { ReactNode } from 'react'
import { render,screen,fireEvent } from '@testing-library/react'
import { beforeEach,expect,it,vi } from 'vitest'
import { TopologyPage } from '../pages/wagpakielaman'
import { layoutTopology } from '../lib/topologyLayout'
import type { TopologyDevice,TopologyData } from '../types/topology'
const api=vi.hoisted(()=>({get:vi.fn(),props:{} as Record<string,unknown>}))
vi.mock('../lib/topologyApi',()=>({getTopology:()=>api.get(),setDeviceParents:vi.fn()}))
vi.mock('../contexts/CurrentUserContext',()=>({useCurrentUser:()=>({hasPermission:()=>false})}))
vi.mock('../contexts/SystemSettingsContext',()=>({useSystemSettings:()=>({settings:{dashboardRefreshRate:'manual'}})}))
vi.mock('../hooks/useDisplayTime',()=>({useDisplayTime:()=>({formatDateTime:(s:string)=>s})}))
vi.mock('@xyflow/react',()=>({ReactFlow:(props:Record<string,unknown>)=>{
 api.props=props
 const nodes=props.nodes as {id:string;data:{label:string}}[]
 return <div>{nodes.map(n=><button key={n.id} onClick={()=> (props.onNodeClick as (e:unknown,n:unknown)=>void)({},n)}>{n.data.label}</button>)}{props.children as ReactNode}</div>
},Background:()=>null,Controls:()=>null,Handle:()=>null,Position:{Top:'top',Bottom:'bottom'}}))
const node=(id:number,parents:number[]=[]):TopologyDevice=>({id,nagios_host_name:`device-${id}`,display_name:null,ip_address:null,os:null,last_seen_at:null,last_check:null,monitoring_state:'monitored',host_state:null,parent_device_ids:parents,editable:true})
const data:TopologyData={devices:[node(1),node(2),node(3,[1,2]),{...node(4),monitoring_state:'paused'}],edges:[{parent_id:1,child_id:3,nagios_eligible:true,omission_reason:null},{parent_id:2,child_id:3,nagios_eligible:true,omission_reason:null}],suggested_gateway_id:null}
beforeEach(()=>api.get.mockReset().mockResolvedValue(data))
it('places shared children below every parent and includes disconnected roots',()=>{
 const nodes=layoutTopology(data).nodes
 expect(nodes).toHaveLength(4)
 for(const id of ['device-1','device-2'])expect(nodes.find(n=>n.id==='device-3')!.position.y).toBeGreaterThan(nodes.find(n=>n.id===id)!.position.y)
 expect(new Set(nodes.map(n=>`${n.position.x},${n.position.y}`)).size).toBe(4)
})
it('uses backend data, fixed layout and device-only panels',async()=>{
 render(<TopologyPage/>);await screen.findByRole('button',{name:'device-3'})
 expect(api.props.nodesDraggable).toBe(false);expect(api.props.nodesConnectable).toBe(false)
 fireEvent.click(screen.getByRole('button',{name:'device-3'}))
 expect(screen.getByText('Device Information')).toBeInTheDocument()
 expect(screen.getByRole('heading',{name:'Parent devices'})).toBeInTheDocument()
 expect(screen.queryByText('View Interface')).not.toBeInTheDocument()
 expect(screen.queryByText('Chart goes here')).not.toBeInTheDocument()
 expect(api.props.edges).toHaveLength(2)
})
it('offers retry and empty states',async()=>{
 api.get.mockRejectedValueOnce(new Error('Cannot load topology')).mockResolvedValue({...data,devices:[],edges:[]})
 render(<TopologyPage/>);expect(await screen.findByRole('alert')).toHaveTextContent('Cannot load topology')
 fireEvent.click(screen.getByRole('button',{name:'Retry'}))
 expect(await screen.findByText('No inventory devices yet.')).toBeInTheDocument()
})
