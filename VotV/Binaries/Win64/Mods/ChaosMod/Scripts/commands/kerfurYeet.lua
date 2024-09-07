local UEHelpers = require("UEHelpers")

return {
    execute = function()
        local kerfus = StaticFindObject("/Game/objects/kerfurOmega_2.kerfurOmega_2_C")
    
        if kerfus:IsValid() then
            local gameInstance = FindFirstOf("GameInstance")
            local GameplayStatics = UEHelpers:GetGameplayStatics()
            local World = UEHelpers:GetWorld()
            

            local FirstPlayerController = UEHelpers:GetPlayerController()
            local Pawn = FirstPlayerController.Pawn
            local Location = Pawn:K2_GetActorLocation()
            local Rotation = Pawn:K2_GetActorRotation()

            local SpawnedActor = World:SpawnActor(kerfus, Location, Rotation, false, nil, nil, false, false)

            if SpawnedActor:IsValid() then
                print("[MyLuaMod] Spawned kerfus")
                local PreBeginPlay = SpawnedActor.ReceiveBeginPlay
                if PreBeginPlay:IsValid() then
                    PreBeginPlay(SpawnedActor)
                end
                SpawnedActor:startKill()
                return true
            else 
                print("[MyLuaMod] Failed to spawn kerfus")
                return false
            end
        else
            print("[MyLuaMod] Failed to spawn kerfus")
            return false
        end
        return false
    end
}
