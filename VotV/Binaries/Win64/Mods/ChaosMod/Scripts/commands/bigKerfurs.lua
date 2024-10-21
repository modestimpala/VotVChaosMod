local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local mainGame = FindFirstOf("mainGamemode_C")
        local allKerfurs = mainGame.allKerfurs
        local allKerfuros = mainGame.allKerfuros
        local Scale3D = {X=2, Y=2, Z=2}
        allKerfurs:ForEach(function(index, kerfur)
            kerfur:get():SetActorScale3D(Scale3D)
        end)
        allKerfuros:ForEach(function(index, kerfuro)
            kerfuro:get():SetActorScale3D(Scale3D)
        end)
        ExecuteWithDelay(180000, function()
            allKerfurs:ForEach(function(index, kerfur)
                kerfur:get():SetActorScale3D({X=1, Y=1, Z=1})
            end)
            allKerfuros:ForEach(function(index, kerfuro)
                kerfuro:get():SetActorScale3D({X=1, Y=1, Z=1})
            end)
        end)
        return true
    end
}