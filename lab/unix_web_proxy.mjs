// Bridge container loopback to the single host Unix socket mounted by the
// Playwright runner. The container itself has Docker networking disabled.
import net from 'node:net'

const socketPath = process.argv[2]
if (!socketPath) throw new Error('Unix socket path is required')

const server = net.createServer((client) => {
  const upstream = net.createConnection(socketPath)
  client.pipe(upstream)
  upstream.pipe(client)
  const close = () => {
    client.destroy()
    upstream.destroy()
  }
  client.on('error', close)
  upstream.on('error', close)
})

server.listen(18080, '127.0.0.1')
