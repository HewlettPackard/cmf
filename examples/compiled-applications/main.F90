program main

  use cmflib, only : cmf_type

  implicit none

  type(cmf_type) :: cmf

  call cmf%initialize("/home/kulkashr/test/mlmd_path", "pipeline_name", "context_name", "execution_name")
  if (.not. cmf%initialized()) then
    write(*,*) "CMF did not initialize successfully"
    error stop 1
  endif

  call cmf%log_metric("test_metric", ["train_loss"], ["1"], 1)
  call cmf%commit_metrics("test_metric")

  call cmf%finalize()

end program main
