locals {
  project_name = "c23-smearbot"
  region       = "eu-west-2"
  
  # Step Function reference
  step_function_arn = aws_sfn_state_machine.c23_smearbot_step_function.arn
}
