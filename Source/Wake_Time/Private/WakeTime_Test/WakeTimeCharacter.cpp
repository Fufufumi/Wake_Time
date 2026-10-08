// Fill out your copyright notice in the Description page of Project Settings.


#include "WakeTime_Test/WakeTimeCharacter.h"

// Sets default values
AWakeTimeCharacter::AWakeTimeCharacter()
{
 	// Set this pawn to call Tick() every frame.  You can turn this off to improve performance if you don't need it.
	PrimaryActorTick.bCanEverTick = true;

}

// Called when the game starts or when spawned
void AWakeTimeCharacter::BeginPlay()
{
	Super::BeginPlay();
	
}

// Called every frame
void AWakeTimeCharacter::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

}

// Called to bind functionality to input
void AWakeTimeCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

}

