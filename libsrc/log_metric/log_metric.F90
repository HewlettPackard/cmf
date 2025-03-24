module cmflib

  use iso_c_binding, only : c_null_char, c_char, c_int

  implicit none
  private

  ! Define interfaces to C-routines
  interface
    subroutine cmf_init(mlmd_path, pipeline_name, context_name, execution_name) bind(C)
      use iso_c_binding, only : c_char
      character(kind=c_char), intent(in) :: mlmd_path(*), pipeline_name(*), context_name(*), execution_name(*)
    end subroutine cmf_init
  end interface

  interface
    integer(kind=c_int) function is_cmf_initialized() bind(C)
      use iso_c_binding, only : c_int
    end function is_cmf_initialized
  end interface

  interface
    subroutine log_metric_c(key, dict_keys, dict_values, dict_size) bind(C, name="log_metric")
      use iso_c_binding, only : c_char, c_int
      character(kind=c_char), intent(in) :: key(*)
      character(kind=c_char), intent(in) :: dict_keys(*)
      character(kind=c_char), intent(in) :: dict_values(*)
      integer(kind=c_int), intent(in) :: dict_size
    end subroutine log_metric_c
  end interface

  interface
    subroutine commit_metrics_c(metrics_name) bind(C, name="commit_metrics")
      use iso_c_binding, only : c_char
      character(kind=c_char), intent(in) :: metrics_name(*)
    end subroutine commit_metrics_c
  end interface

  interface
    subroutine cmf_finalize() bind(C)
    end subroutine cmf_finalize
  end interface

  type, public :: cmf_type

    contains

    procedure :: initialize
    procedure :: initialized
    procedure :: log_metric
    procedure :: commit_metrics
    procedure :: finalize

  end type cmf_type

contains

  !> Initialize CMF with parameters
  subroutine initialize(self, mlmd_path, pipeline_name, context_name, execution_name)
    class(cmf_type), intent(in) :: self
    character(len=*), intent(in) :: mlmd_path, pipeline_name, context_name, execution_name

    if (.not. self%initialized()) then
      call cmf_init(trim(mlmd_path)//c_null_char, trim(pipeline_name)//c_null_char, &
                    trim(context_name)//c_null_char, trim(execution_name)//c_null_char)
    end if

  end subroutine initialize

  !> Check if CMF is initialized
  logical function initialized(self)
    class(cmf_type), intent(in) :: self

    initialized = is_cmf_initialized() == 1
  end function initialized

  !> Log a metric with a key and dictionary of values (key-value pairs)
  subroutine log_metric(self, key, dict_keys, dict_values, dict_size)
    class(cmf_type), intent(in) :: self
    character(len=*), intent(in) :: key
    character(len=*), dimension(:), intent(in) :: dict_keys, dict_values

    integer(kind=c_int) :: dict_size

    dict_size = size(dict_keys)

    call log_metric_c(trim(key)//c_null_char, trim(dict_keys(1))//c_null_char, &
                      trim(dict_values(1))//c_null_char, dict_size)

  end subroutine log_metric

  !> Commit metrics with a given name
  subroutine commit_metrics(self, metrics_name)
    class(cmf_type), intent(in) :: self
    character(len=*), intent(in) :: metrics_name

    call commit_metrics_c(trim(metrics_name)//c_null_char)

  end subroutine commit_metrics

  !> Finalize CMF and clean up resources
  subroutine finalize(self)
    class(cmf_type), intent(in) :: self

    call cmf_finalize()

  end subroutine finalize

end module cmflib
