local UEHelpers = require("UEHelpers")  -- Load UEHelpers

return {
    execute = function()
        local mainGame = FindFirstOf("mainGamemode_C")
        mainGame:addEffect(FName("lsd"), 100, 10, true, true)
        return true
    end
}