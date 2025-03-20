module cmflib

  use iso_c_binding, only : c_null_char, c_char, c_int

  implicit none; private

  ! Define interfaces to C-routines
  interface
    subroutine cmf_init() bind(C)
    end subroutine cmf_init
  end interface

  interface
    integer(kind=c_int) function is_cmf_initialized() bind(C)
    use iso_c_binding, only : c_int
    end function is_cmf_initialized
  end interface

  interface
    subroutine log_metric_c(k, v) bind(C, name="log_metric")
      use iso_c_binding, only : c_char
      character(kind=c_char) :: k(*)
      character(kind=c_char) :: v(*)
    end subroutine log_metric_c
  end interface

  interface
    subroutine commit_metrics_c(k) bind(C, name="commit_metrics")
      use iso_c_binding, only : c_char
      character(kind=c_char) :: k(*)
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

  !> Initialize CMF
  subroutine initialize(self)
    class(cmf_type), intent(in) :: self

    if (.not. self%initialized()) call cmf_init()

  end subroutine initialize

  logical function initialized(self)
    class(cmf_type), intent(in) :: self

    initialized = is_cmf_initialized() == 1
  end function initialized

  subroutine log_metric(self, key, value)
    class(cmf_type),  intent(in) :: self
    character(len=*), intent(in) :: key
    character(len=*), intent(in) :: value

    call log_metric_c(trim(key)//c_null_char, trim(value)//c_null_char)
  end subroutine log_metric

  subroutine commit_metrics(self, key)
    class(cmf_type),  intent(in) :: self
    character(len=*), intent(in) :: key

    call commit_metrics_c(trim(key)//c_null_char)
  end subroutine commit_metrics

  subroutine finalize(self)
    class(cmf_type),  intent(in) :: self

    call cmf_finalize()

  end subroutine finalize

end module cmflib