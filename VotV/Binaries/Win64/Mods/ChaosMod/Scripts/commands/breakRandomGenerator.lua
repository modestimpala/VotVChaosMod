local UEHelpers = require("UEHelpers")  -- Load UEHelpers

return {
    execute = function()
        local mainGame = FindFirstOf("mainGamemode_C")
        local generators = mainGame.generators
        local goodGenerators = {}
        generators:ForEach(function(index, generator)
            if generator:get().IsBroken ~= true then
                table.insert(goodGenerators, generator:get())
            end
        end)
        if #goodGenerators == 0 then
            return false
        else 
            goodGenerators[math.random(#goodGenerators)]['break']()
        end
        return true
    end
}