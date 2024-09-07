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
            local i = 0
            for i = 0, 2 do
                local SpawnedActor = World:SpawnActor(kerfus, Location, Rotation, false, nil, nil, false, false)
                if SpawnedActor:IsValid() then
                    local PreBeginPlay = SpawnedActor.ReceiveBeginPlay
                    if PreBeginPlay:IsValid() then
                        PreBeginPlay(SpawnedActor)
                    end
                    
                    SpawnedActor:doTask()
                    SpawnedActor:makeMeow()
                    print(tostring(SpawnedActor.State))
                end
            end
        
        else
            print("[MyLuaMod] Failed to spawn kerfurs")
            return false
        end
        return false
    end
}