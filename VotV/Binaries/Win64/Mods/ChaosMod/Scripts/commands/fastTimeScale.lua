local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local daynightCycle = FindFirstOf("daynightCycle_C")
        daynightCycle.TimeScale = 100
        ExecuteWithDelay(45000, function()
            daynightCycle.TimeScale = 1
            Hint("Normal speed!")
        end)
        return true
    end
}