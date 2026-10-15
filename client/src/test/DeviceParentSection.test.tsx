import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import type { TopologyData, TopologyDevice } from '../types/topology'
import { DeviceParentSection } from '../components/device-inventory/DeviceParentSection'
const api=vi.hoisted(()=>({get:vi.fn(),put:vi.fn(),edit:true}))
vi.mock('../lib/topologyApi',()=>({getTopology:()=>api.get(),setDeviceParents:(...args:unknown[])=>api.put(...args)}))
vi.mock('../contexts/CurrentUserContext',()=>({useCurrentUser:()=>({hasPermission:()=>api.edit})}))
const node=(id:number,name:string,parents:number[]=[]):TopologyDevice=>({id,nagios_host_name:name,display_name:null,ip_address:null,os:null,last_seen_at:null,last_check:null,monitoring_state:'monitored',host_state:null,parent_device_ids:parents,editable:true})
const data:TopologyData={devices:[node(1,'child'),node(2,'router-a'),node(3,'router-b')],edges:[],suggested_gateway_id:2}
beforeEach(()=>{api.get.mockReset().mockResolvedValue(structuredClone(data));api.put.mockReset().mockResolvedValue({});api.edit=true})
it('searches, sets multiple parents and clears them',async()=>{
 render(<DeviceParentSection deviceId={1}/>)
 await screen.findByRole('checkbox',{name:/router-a/})
 expect(screen.getByText(/Suggested gateway/)).toBeInTheDocument()
 await userEvent.type(screen.getByRole('searchbox'),'router-a')
 expect(screen.queryByRole('checkbox',{name:/router-b/})).not.toBeInTheDocument()
 await userEvent.click(screen.getByRole('checkbox',{name:/router-a/}))
 await userEvent.clear(screen.getByRole('searchbox'))
 await userEvent.click(screen.getByRole('checkbox',{name:/router-b/}))
 await userEvent.click(screen.getByRole('button',{name:'Save parents'}))
 await waitFor(()=>expect(api.put).toHaveBeenCalledWith(1,[2,3]))
 expect(await screen.findByText('Parent devices saved.')).toBeInTheDocument()
 await userEvent.click(screen.getByRole('button',{name:'Clear all'}))
 await userEvent.click(screen.getByRole('button',{name:'Save parents'}))
 await waitFor(()=>expect(api.put).toHaveBeenLastCalledWith(1,[]))
})
it('retains choices and shows server errors',async()=>{
 api.put.mockRejectedValue(new Error('Parent relationships must not create a cycle.'))
 render(<DeviceParentSection deviceId={1}/>)
 await userEvent.click(await screen.findByRole('checkbox',{name:/router-a/}))
 await userEvent.click(screen.getByRole('button',{name:'Save parents'}))
 expect(await screen.findByRole('alert')).toHaveTextContent('Parent relationships must not create a cycle.')
 expect(screen.getByRole('checkbox',{name:/router-a/})).toBeChecked()
})
it('shows existing parents without editing controls for readers',async()=>{
 api.edit=false;api.get.mockResolvedValue({...data,devices:[node(1,'child',[2]),data.devices[1],data.devices[2]]})
 render(<DeviceParentSection deviceId={1}/>)
 expect(await screen.findByText('router-a')).toBeInTheDocument()
 expect(screen.queryByRole('checkbox')).not.toBeInTheDocument()
 expect(screen.queryByRole('button',{name:'Save parents'})).not.toBeInTheDocument()
})
it('retries a load error and warns about paused parents',async()=>{
 api.get.mockRejectedValueOnce(new Error('Unavailable')).mockResolvedValue({...data,devices:[node(1,'child',[2]),{...data.devices[1],monitoring_state:'paused'},data.devices[2]]})
 render(<DeviceParentSection deviceId={1}/>)
 expect(await screen.findByRole('alert')).toHaveTextContent('Unavailable')
 await userEvent.click(screen.getByRole('button',{name:'Retry'}))
 expect(await screen.findByText(/not used by Nagios/)).toBeInTheDocument()
})
it('shows an empty choices state',async()=>{
 api.get.mockResolvedValue({...data,devices:[data.devices[0]],suggested_gateway_id:null})
 render(<DeviceParentSection deviceId={1}/>)
 expect(await screen.findByText('No parent devices available.')).toBeInTheDocument()
})

it('preserves an unsaved draft when topology refreshes',async()=>{
 const {rerender}=render(<DeviceParentSection deviceId={1} topology={data}/>)
 await userEvent.click(await screen.findByRole('checkbox',{name:/router-a/}))
 rerender(<DeviceParentSection deviceId={1} topology={structuredClone(data)}/>)
 await waitFor(()=>expect(screen.getByRole('checkbox',{name:/router-a/})).toBeChecked())
})
