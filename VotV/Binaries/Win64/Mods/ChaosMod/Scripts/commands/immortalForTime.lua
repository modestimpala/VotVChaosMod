local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local mainGame = FindFirstOf("mainGamemode_C")
        mainGame.Immortal = true
        ExecuteWithDelay(180000, function()
            mainGame.Immortal = false
        end)
        return true
    end
}