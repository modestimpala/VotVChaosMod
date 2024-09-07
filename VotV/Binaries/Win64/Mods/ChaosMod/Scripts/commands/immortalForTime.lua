local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local mainGame = FindFirstOf("mainGamemode_C")
        mainGame.Immortal = true
        ExecuteWithDelay(180000, function()
            mainGame.Immortal = false
            Hint("Immortality has ended")
        end)
        return true
    end
}