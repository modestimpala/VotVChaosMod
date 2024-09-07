local UEHelpers = require("UEHelpers")  -- Load UEHelpers

return {
    execute = function()
        local mainGame = FindFirstOf("mainGamemode_C")
        local generators = mainGame.generators
        generators:ForEach(function(index, generator)
            generator:get().cycle = 100
            generator:get().IsBroken = false
            generator:get():turnedOn__DelegateSignature()
        end)
        return true
    end
}