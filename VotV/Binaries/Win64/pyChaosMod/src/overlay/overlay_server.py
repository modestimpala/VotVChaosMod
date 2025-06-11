import asyncio
import json
import logging
import os
from aiohttp import web, WSMsgType
import aiohttp_cors
from typing import Set, Optional

logger = logging.getLogger(__name__)

class OverlayServer:
    def __init__(self, config, voting_system):
        self.config = config
        self.voting_system = voting_system
        self.port = config.get('overlay', {}).get('port', 3202)
        self.app = None
        self.runner = None
        self.site = None
        self.websocket_connections: Set = set()
        self._running = False
        
    async def websocket_handler(self, request):
        """Handle WebSocket connections from the overlay page."""
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        
        self.websocket_connections.add(ws)
        logger.debug("Overlay client connected")
        
        # Send current voting state immediately
        await self.send_voting_update(ws)
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.ERROR:
                    logger.error(f'WebSocket error: {ws.exception()}')
                    break
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.websocket_connections.discard(ws)
            logger.debug("Overlay client disconnected")
            
        return ws
    
    async def send_voting_update(self, ws=None):
        """Send voting update to overlay clients."""
        if not self.websocket_connections and ws is None:
            return
            
        # Get current voting data
        vote_data = {
            "type": "voting_update",
            "active": self.voting_system.voting_active,
            "options": [],
            "total_votes": 0
        }
        
        if self.voting_system.voting_active and hasattr(self.voting_system, 'option_names'):
            total_votes = sum(self.voting_system.votes.values())
            vote_data["total_votes"] = total_votes
            
            for i, option_name in enumerate(self.voting_system.option_names):
                vote_count = self.voting_system.votes.get(i, 0)
                vote_data["options"].append({
                    "index": i + 1,
                    "name": option_name,
                    "votes": vote_count
                })
        
        message = json.dumps(vote_data)
        
        # Send to specific websocket or all connections
        connections_to_send = [ws] if ws else list(self.websocket_connections)
        disconnected = []
        
        for connection in connections_to_send:
            try:
                await connection.send_str(message)
            except Exception as e:
                logger.error(f"Failed to send update to overlay client: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.websocket_connections.discard(conn)
    
    async def send_voting_result(self, winning_option):
        """Send voting result to overlay clients."""
        if not self.websocket_connections:
            return
            
        result_data = {
            "type": "voting_result",
            "winner": winning_option
        }
        
        message = json.dumps(result_data)
        disconnected = []
        
        for ws in list(self.websocket_connections):
            try:
                await ws.send_str(message)
            except Exception as e:
                logger.error(f"Failed to send result to overlay client: {e}")
                disconnected.append(ws)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.websocket_connections.discard(conn)
    
    async def serve_css(self, request):
        """Serve the CSS file from cfg/styles.css."""
        css_path = os.path.join(os.getcwd(), 'cfg', 'styles.css')
        
        try:
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            return web.Response(text=css_content, content_type='text/css')
        except FileNotFoundError:
            # If CSS file doesn't exist, create a default one
            await self.create_default_css(css_path)
            with open(css_path, 'r', encoding='utf-8') as f:
                css_content = f.read()
            return web.Response(text=css_content, content_type='text/css')
        except Exception as e:
            logger.error(f"Error serving CSS file: {e}")
            return web.Response(text="/* Error loading CSS */", content_type='text/css')
    
    async def serve_font(self, request):
        """Serve the font file from cfg/ShareTechMono-Regular.ttf."""
        font_path = os.path.join(os.getcwd(), 'cfg', 'ShareTechMono-Regular.ttf')
        
        try:
            with open(font_path, 'rb') as f:
                font_content = f.read()
            return web.Response(body=font_content, content_type='font/ttf')
        except FileNotFoundError:
            logger.warning(f"Font file not found at {font_path}")
            return web.Response(status=404, text="Font file not found")
        except Exception as e:
            logger.error(f"Error serving font file: {e}")
            return web.Response(status=500, text="Error loading font")
    
    async def create_default_css(self, css_path):
        """Create the default CSS file if it doesn't exist."""
        os.makedirs(os.path.dirname(css_path), exist_ok=True)
        
        default_css = """/* Chaos Mod Voting Overlay */
@font-face {
    font-family: 'ShareTechMono';
    src: url('ShareTechMono-Regular.ttf') format('truetype');
}

body {
    margin: 0;
    padding: 20px;
    font-family: 'ShareTechMono', 'Courier New', monospace;
    background: transparent;
    color: #ffffff;
    overflow: hidden;
}

.overlay-container {
    opacity: 0;
    transition: opacity 0.5s ease-in-out;
    background: rgba(0, 0, 0, 0.85);
    border: 2px solid #444444;
    border-radius: 0;
    padding: 15px 20px;
    max-width: 350px;
    min-width: 300px;
    font-size: 16px;
    letter-spacing: 0.5px;
}

.overlay-container.active {
    opacity: 1;
}

.overlay-container.result {
    background: rgba(0, 100, 0, 0.85);
    border-color: #00ff00;
}

.voting-title {
    font-size: 20px;
    font-weight: normal;
    margin-bottom: 10px;
    text-align: center;
    color: #ffffff;
    letter-spacing: 1px;
}

.voting-option {
    font-size: 16px;
    margin: 2px 0;
    padding: 4px 8px;
    background: transparent;
    border-radius: 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #ffffff;
    line-height: 1.2;
}

.option-text {
    flex-grow: 1;
    text-align: left;
}

.option-votes {
    font-weight: normal;
    background: transparent;
    padding: 0 4px;
    border-radius: 0;
    min-width: 20px;
    text-align: right;
    color: #ffffff;
}

.total-votes {
    text-align: center;
    margin-top: 10px;
    font-size: 14px;
    color: #cccccc;
    letter-spacing: 0.5px;
}

.result-message {
    font-size: 18px;
    text-align: center;
    font-weight: normal;
    color: #00ff00;
    letter-spacing: 1px;
    text-transform: uppercase;
}

.winner-option {
    font-size: 16px;
    margin: 8px 0;
    padding: 8px;
    background: transparent;
    border: 1px solid #00ff00;
    border-radius: 0;
    text-align: center;
    color: #00ff00;
    letter-spacing: 0.5px;
}"""
        
        with open(css_path, 'w', encoding='utf-8') as f:
            f.write(default_css)
        
        logger.info(f"Created default CSS file at {css_path}")
    
    async def overlay_page(self, request):
        """Serve the overlay HTML page."""
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voting Overlay</title>
    <link rel="stylesheet" href="/styles.css">
</head>
<body>
    <div id="overlayContainer" class="overlay-container">
        <div id="votingContent">
            <div class="voting-title">ChaosMod</div>
            <div id="votingOptions"></div>
            <div id="totalVotes" class="total-votes"></div>
        </div>
        <div id="resultContent" style="display: none;">
            <div class="result-message">Winner!</div>
            <div id="winnerOption" class="winner-option"></div>
        </div>
    </div>

    <script>
        let ws;
        let resultTimeout;

        function connectWebSocket() {
            ws = new WebSocket(`ws://${window.location.host}/ws`);
            
            ws.onopen = function() {
                console.log('Connected to overlay WebSocket');
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };
            
            ws.onclose = function() {
                console.log('Overlay WebSocket connection closed');
                setTimeout(connectWebSocket, 3000); // Reconnect after 3 seconds
            };
            
            ws.onerror = function(error) {
                console.error('Overlay WebSocket error:', error);
            };
        }

        function handleMessage(data) {
            if (data.type === 'voting_update') {
                updateVotingDisplay(data);
            } else if (data.type === 'voting_result') {
                showResult(data.winner);
            }
        }

        function updateVotingDisplay(data) {
            const container = document.getElementById('overlayContainer');
            const votingContent = document.getElementById('votingContent');
            const resultContent = document.getElementById('resultContent');
            
            // Don't hide if we're currently showing results
            if (resultTimeout && !data.active) {
                return; // Ignore voting updates when showing results
            }
            
            // Clear any result timeout
            if (resultTimeout) {
                clearTimeout(resultTimeout);
                resultTimeout = null;
            }
            
            if (data.active && data.options.length > 0) {
                // Show voting content
                votingContent.style.display = 'block';
                resultContent.style.display = 'none';
                container.className = 'overlay-container active';
                
                // Update options
                const optionsContainer = document.getElementById('votingOptions');
                optionsContainer.innerHTML = '';
                
                data.options.forEach(option => {
                    const optionDiv = document.createElement('div');
                    optionDiv.className = 'voting-option';
                    optionDiv.innerHTML = `
                        <span class="option-text">${option.index}. ${option.name}</span>
                        <span class="option-votes">${option.votes}</span>
                    `;
                    optionsContainer.appendChild(optionDiv);
                });
                
                // Update total votes
                document.getElementById('totalVotes').textContent = `Total Votes: ${data.total_votes}`;
            } else {
                // Hide overlay only if we're not showing results
                if (!resultTimeout) {
                    container.className = 'overlay-container';
                }
            }
        }

        function showResult(winner) {
            const container = document.getElementById('overlayContainer');
            const votingContent = document.getElementById('votingContent');
            const resultContent = document.getElementById('resultContent');
            const winnerOption = document.getElementById('winnerOption');
            
            // Show result
            votingContent.style.display = 'none';
            resultContent.style.display = 'block';
            winnerOption.textContent = winner;
            container.className = 'overlay-container active result';
            
            // Hide after 5 seconds
            resultTimeout = setTimeout(() => {
                container.className = 'overlay-container';
            }, 5000);
        }

        // Connect when page loads
        connectWebSocket();
    </script>
</body>
</html>"""
        
        return web.Response(text=html_content, content_type='text/html')
    
    async def start(self):
        """Start the overlay web server."""
        if self._running:
            logger.warning("Overlay server is already running")
            return
            
        try:
            self.app = web.Application()
            
            # Add CORS support
            cors = aiohttp_cors.setup(self.app, defaults={
                "*": aiohttp_cors.ResourceOptions(
                    allow_credentials=True,
                    expose_headers="*",
                    allow_headers="*",
                    allow_methods="*"
                )
            })
            
            # Add routes
            self.app.router.add_get('/', self.overlay_page)
            self.app.router.add_get('/ws', self.websocket_handler)
            self.app.router.add_get('/styles.css', self.serve_css)
            self.app.router.add_get('/ShareTechMono-Regular.ttf', self.serve_font)
            
            # Add CORS to all routes
            for route in list(self.app.router.routes()):
                cors.add(route)
            
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(self.runner, 'localhost', self.port)
            await self.site.start()
            
            self._running = True
            logger.info(f"Overlay server started on http://localhost:{self.port}")
            
            # Keep the server running indefinitely - this is crucial for TaskManager
            try:
                while self._running:
                    await asyncio.sleep(1)
            finally:
                await self.stop()
            
        except Exception as e:
            self._running = False
            logger.error(f"Failed to start overlay server: {e}")
            raise

    async def stop(self):
        """Stop the overlay server."""
        if not self._running:
            return
            
        logger.info("Stopping overlay server...")
        self._running = False  # Signal the running loop to stop
            
        try:
            # Close all WebSocket connections
            for ws in list(self.websocket_connections):
                await ws.close()
            self.websocket_connections.clear()
            
            # Stop the server
            if self.site:
                await self.site.stop()
                self.site = None
                
            if self.runner:
                await self.runner.cleanup()
                self.runner = None
                
            self.app = None
            logger.info("Overlay server stopped")
            
        except Exception as e:
            logger.error(f"Error stopping overlay server: {e}")
        finally:
            self._running = False

    async def update_config(self, new_config):
        """Update the configuration."""
        self.config = new_config
        new_port = new_config.get('overlay', {}).get('port', 3202)
        if new_port != self.port:
            logger.info(f"Overlay server port changed from {self.port} to {new_port}")
            await self.stop()
            self.port = new_port
            await self.start()