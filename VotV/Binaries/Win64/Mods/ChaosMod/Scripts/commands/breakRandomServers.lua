local UEHelpers = require("UEHelpers")  -- Load UEHelpers

return {
    execute = function()
        local mainGame = FindFirstOf("mainGamemode_C")
        local servers = mainGame.servers
        local goodServers = {}
        servers:ForEach(function(index, server)
            if server:get().broken_0 ~= true then
                table.insert(goodServers, server:get())
            end
        end)
        
        -- Shuffle the goodServers table
        for i = #goodServers, 2, -1 do
            local j = math.random(i)
            goodServers[i], goodServers[j] = goodServers[j], goodServers[i]
        end
        
        -- Break up to 3 servers
        for i = 1, math.min(3, #goodServers) do
            goodServers[i]:breakServer()
        end
        return true
    end
}