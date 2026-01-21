program main

  use cmflib, only : cmf_type

  implicit none

  type(cmf_type) :: cmf
  character(len=24), dimension(2) :: keys, values

  keys(1) = "foo"
  keys(2) = "bar"
  values(1) = "10"
  values(2) = "3.14"

  call cmf%initialize("/tmp/shao/test/mlmd_path", "pipeline_name", "context_name", "execution_name")
  if (.not. cmf%initialized()) then
    write(*,*) "CMF did not initialize successfully"
    error stop 1
  endif

  call cmf%log_metric("test_metric", keys, values)
  call cmf%commit_metrics("test_metric")

  call cmf%finalize()

end program main
